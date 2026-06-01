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
from pytex_markdown.convert import CALLOUT_RE, MarkdownConverter

from .entries import ActionItem, Deadline, Decision, Vote
from .shortcodes import expand_inline_shortcodes

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from pytex.interface.tex import TeX

    from .frontmatter import FrontmatterValue

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


def _all_text(node: object) -> str:
    """Concatenate every literal text fragment beneath `node`."""
    text = _text(node)
    if text is not None:
        return text
    return "".join(_all_text(c) for c in _children(node))


def _tally(text: str, key: str) -> int:
    match = _TALLY_RE[key].search(text)
    return int(match.group(1)) if match else 0


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
            return self._vote_callout(title, kids)
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
        if name not in _PROTOCOL_CALLOUTS and name not in _VOTE_MARKERS:
            return None
        title = first[match.end() :].strip()
        return name, title, inner[1:], kids[1:]

    def _vote_callout(self, title: str, kids: list[object]) -> TeX:
        text = " ".join(_all_text(k) for k in kids)
        return Vote(
            yes=_tally(text, "yes"),
            no=_tally(text, "no"),
            abstain=_tally(text, "abstain"),
            body=self.inline_text(title) if title else "",
        )

    def inline_text(self, text: str) -> TeX:
        """Expand `{{shortcodes}}` and escape the rest of a bare string."""
        return expand_inline_shortcodes(text, self.meta)


def _join(blocks: list[TeX]) -> list[TeX]:
    from pytex.model.empty import Empty
    from pytex.model.raw import Raw

    parbreak = Raw("\n\n")
    kept = [b for b in blocks if b is not Empty]
    out: list[TeX] = []
    for i, b in enumerate(kept):
        if i:
            out.append(parbreak)
        out.append(b)
    return out
