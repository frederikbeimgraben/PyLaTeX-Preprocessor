"""Convert a marko Markdown AST into native PyTeX ``TeX`` nodes.

Block elements map to the standard pytex library (headings, lists, quotes,
code, rules); inline elements map to text-formatting commands. GitHub-style
callouts (``> [!NOTE]`` ...) become HSRT ``ColoredBox`` presets, which is why
this module depends on ``pytex_hsrtreport``.
"""

from __future__ import annotations

import re
from typing import Callable, Final, cast, final

from pytex.commands.builtin import (
    Bold,
    Emph,
    Enumerate,
    Itemize,
    Newline,
    Part,
    Chapter,
    Section,
    Subsection,
    Subsubsection,
    Paragraph,
    Subparagraph,
    Quote,
    Texttt,
    Verbatim,
    Noindent,
    Rule,
)
from pytex.commands.hyperref import Href
from pytex.interface.tex import TeX
from pytex.model.concat import Concat
from pytex.model.empty import Empty
from pytex.model.image import IncludeImage
from pytex.model.raw import Raw

from pytex_hsrtreport.boxes import ImportantBox, InfoBox, SuccessBox, WarningBox

from .escape import escape_latex

# Heading commands ordered from the broadest division downward. The default
# `base_level` of 0 maps Markdown ``#`` (level 1) to ``Section``.
_HEADINGS: Final[tuple[Callable[..., TeX], ...]] = (
    Part,
    Chapter,
    Section,
    Subsection,
    Subsubsection,
    Paragraph,
    Subparagraph,
)
_SECTION_INDEX: Final[int] = 2  # index of Section in _HEADINGS

_CALLOUT_RE: Final[re.Pattern[str]] = re.compile(r"^\s*\[!(\w+)\]\s*", re.IGNORECASE)
_CALLOUTS: Final[dict[str, Callable[[TeX | str], TeX]]] = {
    "NOTE": InfoBox,
    "INFO": InfoBox,
    "TIP": SuccessBox,
    "HINT": SuccessBox,
    "SUCCESS": SuccessBox,
    "IMPORTANT": ImportantBox,
    "WARNING": WarningBox,
    "CAUTION": WarningBox,
    "DANGER": WarningBox,
    "ERROR": WarningBox,
}

_PARBREAK: Final[TeX] = Raw("\n\n")


def _kind(node: object) -> str:
    return type(node).__name__


def _children(node: object) -> list[object]:
    ch = getattr(node, "children", None)
    return cast("list[object]", ch) if isinstance(ch, list) else []


def _text(node: object) -> str | None:
    """Return a node's literal text payload, or ``None`` for container nodes."""
    ch = getattr(node, "children", None)
    return ch if isinstance(ch, str) else None


@final
class MarkdownConverter:
    """Walk a marko AST, producing a single ``TeX`` tree."""

    base_level: int
    callouts: bool

    def __init__(self, *, base_level: int = 0, callouts: bool = True) -> None:
        self.base_level = base_level
        self.callouts = callouts

    # -- inline -----------------------------------------------------------

    def inline(self, node: object) -> TeX:
        kind = _kind(node)
        text = _text(node)
        if text is not None:
            # RawText / CodeSpan / Literal etc. carry a plain string.
            if kind == "CodeSpan":
                return Texttt(Raw(escape_latex(text)))
            return Raw(escape_latex(text))

        if kind == "StrongEmphasis":
            return Bold(self.inlines(node))
        if kind == "Emphasis":
            return Emph(self.inlines(node))
        if kind == "Link":
            dest = str(getattr(node, "dest", ""))
            return Href(dest, self.inlines(node))
        if kind == "Image":
            return IncludeImage(str(getattr(node, "dest", "")))
        if kind == "LineBreak":
            # Hard break -> newline; soft break -> a plain space.
            soft = bool(getattr(node, "soft", False))
            return Raw(" ") if soft else Newline()

        # Unknown inline: recurse if it has children, else drop.
        kids = _children(node)
        return self.inlines(node) if kids else Empty

    def inlines(self, node: object) -> TeX:
        return Concat(*(self.inline(c) for c in _children(node)))

    # -- blocks -----------------------------------------------------------

    def _heading(self, node: object) -> TeX:
        level = int(getattr(node, "level", 1))
        idx = _SECTION_INDEX + (level - 1) + self.base_level
        idx = max(0, min(idx, len(_HEADINGS) - 1))
        return _HEADINGS[idx](self.inlines(node))

    def _list(self, node: object) -> TeX:
        items = [self._list_item(c) for c in _children(node) if _kind(c) == "ListItem"]
        factory = Enumerate if bool(getattr(node, "ordered", False)) else Itemize
        return factory(*items)

    def _list_item(self, node: object) -> TeX:
        kids = _children(node)
        # Tight item: a lone paragraph -> inline its content (no extra break).
        if len(kids) == 1 and _kind(kids[0]) == "Paragraph":
            return self.inlines(kids[0])
        return self.blocks(kids)

    def _quote(self, node: object) -> TeX:
        kids = _children(node)
        callout = self._as_callout(kids) if self.callouts else None
        if callout is not None:
            return callout
        return Quote(self.blocks(kids))

    def _as_callout(self, kids: list[object]) -> TeX | None:
        if not kids or _kind(kids[0]) != "Paragraph":
            return None
        inner = _children(kids[0])
        first_text = _text(inner[0]) if inner else None
        if first_text is None:
            return None
        match = _CALLOUT_RE.match(first_text)
        if match is None:
            return None
        box = _CALLOUTS.get(match.group(1).upper())
        if box is None:
            return None
        # Rebuild the first paragraph with the marker stripped, keep the rest.
        stripped = first_text[match.end():]
        head = Concat(
            Raw(escape_latex(stripped)),
            *(self.inline(c) for c in inner[1:]),
        )
        body_blocks = [head, *(self.block(b) for b in kids[1:])]
        return box(Concat(*_interleave(body_blocks)))

    def _code(self, node: object) -> TeX:
        # Code blocks hold a single RawText child; fall back to a direct string.
        text = _text(node)
        if text is None:
            kids = _children(node)
            text = _text(kids[0]) if kids else ""
        return Verbatim((text or "").rstrip("\n"))

    def _rule(self, _node: object) -> TeX:
        return Concat(Noindent(), Rule(r"\linewidth", "0.4pt"))

    def block(self, node: object) -> TeX:
        kind = _kind(node)
        if kind == "Heading":
            return self._heading(node)
        if kind == "Paragraph":
            return self.inlines(node)
        if kind == "List":
            return self._list(node)
        if kind == "Quote":
            return self._quote(node)
        if kind in ("FencedCode", "CodeBlock"):
            return self._code(node)
        if kind == "ThematicBreak":
            return self._rule(node)
        if kind in ("BlankLine", "LinkRefDef"):
            return Empty
        # Container we do not special-case (e.g. nested Document).
        kids = _children(node)
        return self.blocks(kids) if kids else Empty

    def blocks(self, nodes: list[object]) -> TeX:
        out = [self.block(n) for n in nodes if _kind(n) not in ("BlankLine",)]
        return Concat(*_interleave(out))


def _interleave(blocks: list[TeX]) -> list[TeX]:
    """Join block nodes with paragraph breaks, dropping empties."""
    kept = [b for b in blocks if b is not Empty]
    joined: list[TeX] = []
    for i, b in enumerate(kept):
        if i:
            joined.append(_PARBREAK)
        joined.append(b)
    return joined
