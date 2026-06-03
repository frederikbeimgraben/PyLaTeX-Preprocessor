"""A Markdown converter for meeting protocols.

Extends the base :class:`pytex_markdown.convert.MarkdownConverter` with:

* protocol callouts - ``> [!beschluss]``, ``> [!abstimmung]`` (parsed into a
  vote tally), ``> [!aufgabe]``, ``> [!frist]`` - on top of the inherited
  GitHub/Obsidian callouts;
* inline ``{{shortcode}}`` expansion in every run of text.

Agenda items (TOPs) are plain Markdown headings, so they need no special
handling - they become numbered sections via the base converter.
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

# Callout marker -> single-body entry factory.
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
    """A line is the vote tally if it carries at least two of yes/no/abstain."""
    return sum(1 for rx in _TALLY_RE.values() if rx.search(line)) >= 2


def _interleave(items: Iterator[TeX]) -> Iterator[TeX]:
    """Yield `items` separated by LaTeX line breaks (for multi-line box bodies)."""
    from pytex.model.raw import Raw

    sep = Raw(r"\\")
    for i, item in enumerate(items):
        if i:
            yield sep
        yield item


def _leaf_texts(node: object) -> list[str]:
    """Every leaf text fragment beneath `node`, in order (one per source line)."""
    text = _text(node)
    if text is not None:
        return [text]
    return [frag for child in _children(node) for frag in _leaf_texts(child)]


class ProtocolConverter(MarkdownConverter):
    """`MarkdownConverter` with protocol callouts and inline shortcodes."""

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

    # -- inline: splice {{shortcodes}} into otherwise-plain text ----------

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
        # First paragraph: marker title + its remaining inlines; then any
        # following blocks of the callout.
        head = Concat(self.inline_text(title), *(self.inline(c) for c in head_rest))
        body_parts = [head, *(self.block(b) for b in rest_blocks)]
        return factory(Concat(*_join(body_parts)))

    def _protocol_marker(
        self, kids: list[object]
    ) -> tuple[str, str, list[object], list[object]] | None:
        """Return (MARKER, title-after-marker, rest-of-first-paragraph,
        following-blocks) if kids open a protocol callout we own, else None."""
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
        # Each line "Rolle: Name" becomes one signer; the marker is stripped
        # from the first line.
        lines = [frag for k in kids for frag in _leaf_texts(k)]
        if lines:
            lines[0] = CALLOUT_RE.sub("", lines[0], count=1)
        signers: list[tuple[str, str]] = []
        for line in (entry.strip() for entry in lines):
            if not line:
                continue
            role, _, person = line.partition(":")
            signers.append((role.strip(), person.strip()))
        return SignatureLines(*signers)

    def _vote_callout(self, kids: list[object]) -> TeX:
        # Per source line: the tally line feeds the counts, every other line is
        # kept as the box body (otherwise descriptive text would be dropped).
        lines = [frag for k in kids for frag in _leaf_texts(k)]
        if lines:
            lines[0] = CALLOUT_RE.sub("", lines[0], count=1)
        stripped = [s.strip() for s in lines]
        full = " ".join(stripped)
        body_lines = [s for s in stripped if s and not _is_tally_line(s)]
        body = Concat(*_interleave(self.inline_text(s) for s in body_lines))
        return Vote(
            yes=_tally(full, "yes"),
            no=_tally(full, "no"),
            abstain=_tally(full, "abstain"),
            body=body,
        )

    def inline_text(self, text: str) -> TeX:
        """Expand `{{shortcodes}}` and escape the rest of a bare string."""
        return expand_inline_shortcodes(text, self.meta)


def _join(blocks: list[TeX]) -> Iterator[TeX]:
    from pytex.model.empty import Empty
    from pytex.model.raw import Raw

    parbreak = Raw("\n\n")
    kept = [b for b in blocks if b is not Empty]
    return (part for i, b in enumerate(kept) for part in ((parbreak, b) if i else (b,)))
