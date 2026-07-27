"""A Markdown converter for meeting protocols.

`ProtocolConverter` extends `pytex_markdown.convert.MarkdownConverter` in two
ways:

1. It adds the protocol callouts `> [!beschluss]` (resolution),
   `> [!abstimmung]` (vote, which it parses into a tally), `> [!aufgabe]`
   (action item) and `> [!frist]` (deadline). The GitHub-style callouts of the
   base converter stay available.
2. It expands an inline `{{shortcode}}` in every run of text.

Agenda items (TOPs) are plain Markdown headings, so they need no special
handling. The base converter turns them into numbered sections.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final, cast, override

from pytex.model.concat import Concat

from ..convert import CALLOUT_RE, MarkdownConverter
from .entries import ActionItem, Deadline, Decision, Vote
from .shortcodes import expand_inline_shortcodes
from .signatures import SignatureLines

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Mapping

    from pytex.interface.tex import TeX

    from ..frontmatter import FrontmatterValue

__all__ = ["ProtocolConverter"]

# Callout marker -> the entry factory that takes a single body.
_PROTOCOL_CALLOUTS: Final[dict[str, Callable[[TeX | str], TeX]]] = {
    "BESCHLUSS": Decision,
    "DECISION": Decision,
    "AUFGABE": ActionItem,
    "TODO": ActionItem,
    "ACTION": ActionItem,
    "FRIST": Deadline,
    "DEADLINE": Deadline,
}
_VOTE_MARKERS: Final[frozenset[str]] = frozenset({"ABSTIMMUNG", "VOTE"})
_SIGNATURE_MARKERS: Final[frozenset[str]] = frozenset({"UNTERSCHRIFTEN", "SIGNATURES"})

_TALLY_RE: Final[dict[str, re.Pattern[str]]] = {
    "yes": re.compile(r"(?:ja|yes)\s*[:=]?\s*(\d+)", re.IGNORECASE),
    "no": re.compile(r"(?:nein|no)\s*[:=]?\s*(\d+)", re.IGNORECASE),
    "abstain": re.compile(r"(?:enthaltung|enth\.?|abstain)\s*[:=]?\s*(\d+)", re.I),
}


def _kind(node: object) -> str:
    return type(node).__name__


def _text(node: object) -> str | None:
    children = getattr(node, "children", None)
    return children if isinstance(children, str) else None


def _children(node: object) -> list[object]:
    children = getattr(node, "children", None)
    return cast("list[object]", children) if isinstance(children, list) else []


def _tally(text: str, key: str) -> int:
    match = _TALLY_RE[key].search(text)
    return int(match.group(1)) if match else 0


def _is_tally_line(line: str) -> bool:
    """Test whether a line carries at least two of the three vote counts."""
    return sum(1 for rx in _TALLY_RE.values() if rx.search(line)) >= 2


def _interleave(items: Iterator[TeX]) -> Iterator[TeX]:
    """Yield `items` with a LaTeX line break between them, for a multi-line box."""
    from pytex.model.raw import Raw

    sep = Raw(r"\\")
    for i, item in enumerate(items):
        if i:
            yield sep
        yield item


def _leaf_texts(node: object) -> list[str]:
    """Return every leaf text fragment under `node`, one per source line."""
    text = _text(node)
    if text is not None:
        return [text]
    return [frag for child in _children(node) for frag in _leaf_texts(child)]


class ProtocolConverter(MarkdownConverter):
    """A `MarkdownConverter` with protocol callouts and inline shortcodes.

    Attributes:
        meta: The parsed frontmatter. The shortcode expansion reads the
            meeting fields from it.
    """

    meta: Mapping[str, FrontmatterValue]

    def __init__(
        self,
        *,
        meta: Mapping[str, FrontmatterValue] | None = None,
        base_level: int = 0,
        callouts: bool = True,
    ) -> None:
        super().__init__(base_level=base_level, callouts=callouts)
        self.meta = meta or {}

    # -- inline: expand {{shortcodes}} inside otherwise-plain text --------

    @override
    def inline(self, node: object) -> TeX:
        if _kind(node) != "CodeSpan":
            text = _text(node)
            if text is not None and "{{" in text:
                return expand_inline_shortcodes(text, self.meta)
        return super().inline(node)

    # -- blocks: protocol callouts ----------------------------------------

    @override
    def _as_callout(self, kids: list[object]) -> TeX | None:
        marker = self._protocol_marker(kids)
        if marker is None:
            return super()._as_callout(kids)
        name, title, head_rest, rest_blocks = marker
        if name in _VOTE_MARKERS:
            return self._vote_callout(kids)
        if name in _SIGNATURE_MARKERS:
            return self._signature_callout(kids)
        factory = _PROTOCOL_CALLOUTS.get(name)
        if factory is None:
            return super()._as_callout(kids)
        head = Concat(self.inline_text(title), *(self.inline(c) for c in head_rest))
        body_parts = [head, *(self.block(b) for b in rest_blocks)]
        return factory(Concat(*_join(body_parts)))

    def _protocol_marker(
        self, kids: list[object]
    ) -> tuple[str, str, list[object], list[object]] | None:
        """Read the opening paragraph of a quote as a protocol callout marker.

        Returns:
            A tuple of the marker name, the title after the marker, the rest
            of the first paragraph and the blocks that follow. Returns `None`
            when the quote opens no callout that this class owns.
        """
        if not kids or _kind(kids[0]) != "Paragraph":
            return None
        inner = _children(kids[0])
        first = _text(inner[0]) if inner else None
        if first is None:
            return None
        match = CALLOUT_RE.match(first)
        if match is None:
            return None
        name = match.group(1).upper()
        if (
            name not in _PROTOCOL_CALLOUTS
            and name not in _VOTE_MARKERS
            and name not in _SIGNATURE_MARKERS
        ):
            return None
        title = first[match.end() :].strip()
        return name, title, inner[1:], kids[1:]

    def _signature_callout(self, kids: list[object]) -> TeX:
        # Each line `Rolle: Name` (role, then name) becomes one signer. The
        # first line loses the callout marker.
        lines = [frag for k in kids for frag in _leaf_texts(k)]
        if lines:
            lines[0] = CALLOUT_RE.sub("", lines[0], count=1)
        signers = [
            (role.strip(), person.strip())
            for entry in lines
            if (line := entry.strip())
            for role, _, person in (line.partition(":"),)
        ]
        return SignatureLines(*signers)

    def _vote_callout(self, kids: list[object]) -> TeX:
        # The tally line gives the counts. Every other source line stays as
        # the box body, so the box keeps the descriptive text.
        lines = [frag for k in kids for frag in _leaf_texts(k)]
        if lines:
            lines[0] = CALLOUT_RE.sub("", lines[0], count=1)
        stripped = [s.strip() for s in lines]
        # Only the tally line carries the counts. A descriptive line can
        # contain a stray "ja <digits>" of its own, so the search must not
        # widen to the whole callout.
        tally_line = next((s for s in stripped if _is_tally_line(s)), "")
        body_lines = [s for s in stripped if s and not _is_tally_line(s)]
        body = Concat(*_interleave(self.inline_text(s) for s in body_lines))
        return Vote(
            yes=_tally(tally_line, "yes"),
            no=_tally(tally_line, "no"),
            abstain=_tally(tally_line, "abstain"),
            body=body,
        )

    def inline_text(self, text: str) -> TeX:
        """Expand each `{{shortcode}}` in a bare string and escape the rest."""
        return expand_inline_shortcodes(text, self.meta)


def _join(blocks: list[TeX]) -> Iterator[TeX]:
    from pytex.model.empty import Empty
    from pytex.model.raw import Raw

    parbreak = Raw("\n\n")
    kept = [b for b in blocks if b is not Empty]
    return (part for i, b in enumerate(kept) for part in ((parbreak, b) if i else (b,)))
