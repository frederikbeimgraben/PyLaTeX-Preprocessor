# pyright: reportAny=false, reportExplicitAny=false
"""Convert a marko Markdown AST into native PyTeX ``TeX`` nodes.

Block elements map to the standard pytex library (headings, lists, quotes,
code, rules); inline elements map to text-formatting commands. GitHub-style
callouts (``> [!NOTE]`` ...) become HSRT ``ColoredBox`` presets, which is why
this module depends on ``pytex_hsrtreport``.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, cast

from pytex.commands.biblatex import Autocite, Textcite
from pytex.commands.builtin import (
    Bold,
    Chapter,
    Emph,
    Enumerate,
    Euro,
    Itemize,
    Newline,
    Noindent,
    Paragraph,
    Part,
    Quote,
    Rule,
    Section,
    Subparagraph,
    Subsection,
    Subsubsection,
    Texttt,
)
from pytex.commands.hyperref import Href
from pytex.commands.listings import Lstlisting
from pytex.commands.tables import Bottomrule, Midrule, Tabularx, Toprule
from pytex.interface.tex import TeX
from pytex.model.concat import Concat
from pytex.model.empty import Empty
from pytex.model.image import IncludeImage
from pytex.model.raw import Raw, pytex_namespace
from pytex_components.boxes import ImportantBox, InfoBox, SuccessBox, WarningBox

from .escape import escape_latex

__all__ = ["MarkdownConverter"]

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

# Heading commands ordered from the broadest division downward. The default
# `base_level` of 0 maps Markdown ``#`` (level 1) to ``Section``.
HEADINGS: Final[tuple[Callable[..., TeX], ...]] = (
    Part,
    Chapter,
    Section,
    Subsection,
    Subsubsection,
    Paragraph,
    Subparagraph,
)
SECTION_INDEX: Final[int] = 2  # index of Section in HEADINGS

CALLOUT_RE: Final[re.Pattern[str]] = re.compile(r"^\s*\[!(\w+)\]\s*", re.IGNORECASE)

# Links with a URL scheme (``https:``, ``mailto:`` ...) or protocol-relative
# ``//`` are the only ones that survive as clickable ``\href``. A relative or
# in-document target (``LICENSE``, ``docs/x.md``, ``#section``) points at a
# repo file that does not exist in the rendered PDF -- hyperref would turn it
# into a dead ``LICENSE.pdf`` link -- so those keep their text and drop the URL.
EXTERNAL_URL_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?:[a-z][a-z0-9+.\-]*:|//)", re.IGNORECASE
)

# ASCII arrows in prose -> inline math arrows. All targets are base-LaTeX
# macros, so no extra package is pulled in. ``<=`` is deliberately absent: it
# overwhelmingly means "less than or equal" in prose, not a left arrow.
ARROWS: Final[dict[str, str]] = {
    "<-->": r"\longleftrightarrow",
    "<->": r"\leftrightarrow",
    "<=>": r"\Leftrightarrow",
    "-->": r"\longrightarrow",
    "<--": r"\longleftarrow",
    "->": r"\rightarrow",
    "<-": r"\leftarrow",
    "=>": r"\Rightarrow",
}
# Longest alternatives first so e.g. ``<-->`` wins over ``<-``.
ARROW_RE: Final[re.Pattern[str]] = re.compile(
    "|".join(re.escape(token) for token in sorted(ARROWS, key=len, reverse=True))
)
# Capturing variant: ``re.split`` keeps the matched arrows as odd-indexed
# pieces, so escaping prose and substituting arrows is a single pass.
ARROW_SPLIT_RE: Final[re.Pattern[str]] = re.compile(f"({ARROW_RE.pattern})")
CALLOUTS: Final[dict[str, Callable[[TeX | str], TeX]]] = {
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

# U+20AC EURO SIGN. The DIN text font has no euro glyph, so the raw char would
# render as tofu; we splice in a real ``Euro`` node (eurosym ``\euro{}``) which
# ships its own glyph and registers the package requirement.
EURO_SIGN: Final[str] = "€"

# Pandoc-style citations in prose. A bracketed ``[@key]`` / ``[@key, p. 5]`` /
# ``[@a; @b]`` becomes ``\autocite``; a narrative ``@key`` becomes ``\textcite``.
# Keys use the usual BibTeX charset. The narrative form needs a non-word, non-``@``
# char before it so an e-mail remnant like ``foo@bar`` is never mistaken for a
# cite (e-mails arrive as their own ``Url`` node anyway).
# A BibTeX key starts with an alphanumeric/underscore and, like Pandoc, may
# contain internal punctuation but must not END on it (so a trailing sentence
# period such as ``@knuth.`` is not swallowed into the key).
_CITE_KEY = r"[A-Za-z0-9_](?:[\w:.#$%&+?<>~/-]*[A-Za-z0-9_])?"
CITATION_RE: Final[re.Pattern[str]] = re.compile(
    r"\[(?P<bracket>\s*@[^\]]+)\]" + rf"|(?<![\w@])@(?P<narrative>{_CITE_KEY})"
)
_CITE_ENTRY_RE: Final[re.Pattern[str]] = re.compile(
    rf"^@(?P<key>{_CITE_KEY})\s*(?:,\s*(?P<post>.+))?$"
)

PARBREAK: Final[TeX] = Raw("\n\n")

# Vertical breathing room added above and below a rendered table. ``\addvspace``
# (rather than ``\vspace``) coalesces with adjacent spacing so a table next to a
# heading or another block does not accumulate a double gap.
TABLE_VSPACE: Final[str] = r"0.8\baselineskip"

# GFM cell alignment -> tabularx ``X`` column spec. ``X`` columns share the
# table width and wrap their content, so wide tables no longer overrun the
# page. ``None`` (no colon) falls back to left, matching how most renderers
# treat an unaligned column.
COLUMN_ALIGN: Final[dict[str | None, str]] = {
    "left": r">{\raggedright\arraybackslash}X",
    "center": r">{\centering\arraybackslash}X",
    "right": r">{\raggedleft\arraybackslash}X",
    None: r">{\raggedright\arraybackslash}X",
}


def _kind(node: object) -> str:
    return type(node).__name__


def _children(node: object) -> list[object]:
    ch = getattr(node, "children", None)
    return cast("list[object]", ch) if isinstance(ch, list) else []


def _text(node: object) -> str | None:
    """Return a node's literal text payload, or ``None`` for container nodes."""
    ch = getattr(node, "children", None)
    return ch if isinstance(ch, str) else None


def _escape_text(text: str) -> str:
    """LaTeX-escape prose, turning ASCII arrows into inline math arrows.

    Only used for running text (not code spans/blocks), so ``->`` and friends
    become ``$\\rightarrow$`` etc. while the surrounding text is escaped.
    """
    # ``re.split`` with the capturing group alternates prose / arrow / prose /
    # ...; odd pieces are the matched arrows, even pieces the text around them.
    return "".join(
        f"${ARROWS[piece]}$" if index % 2 else escape_latex(piece)
        for index, piece in enumerate(ARROW_SPLIT_RE.split(text))
    )


def _prose(text: str) -> TeX:
    """Escape prose, splitting literal euro signs into ``Euro`` nodes.

    Each ``€`` becomes a real :func:`Euro` node (eurosym ``\\euro{}``) instead
    of a raw char so the preamble auto-loads ``eurosym`` and the glyph renders
    even under the DIN font. Text between the euros keeps its arrow/escape
    handling, and the split preserves surrounding spacing exactly (e.g. ``50€``
    stays glyph-adjacent, ``€ 50`` keeps its space).
    """
    if EURO_SIGN not in text:
        return Raw(_escape_text(text))
    # Each split point gets a ``Euro`` node (all but the first segment); each
    # non-empty segment its escaped text. Empty segments (``50€€`` / leading
    # ``€``) drop their text but keep the euro, preserving spacing exactly.
    return Concat(
        *(
            node
            for i, segment in enumerate(text.split(EURO_SIGN))
            for node in (
                *((Euro(),) if i else ()),
                *((Raw(_escape_text(segment)),) if segment else ()),
            )
        )
    )


def _citation(match: re.Match[str]) -> TeX | None:
    """Build a cite node from a ``CITATION_RE`` match, or ``None`` if not a cite.

    Narrative ``@key`` -> ``\\textcite``. Bracketed ``[@key]`` -> ``\\autocite``;
    a single key may carry a postnote (``[@key, p. 5]``) and several keys may be
    separated by ``;`` (``[@a; @b]``). A malformed bracket (no valid ``@key``
    inside) returns ``None`` so it falls back to plain escaped text.
    """
    narrative = match.group("narrative")
    if narrative is not None:
        return Textcite(narrative)
    keys: list[str] = []
    postnote: str | None = None
    for entry in match.group("bracket").split(";"):
        parsed = _CITE_ENTRY_RE.match(entry.strip())
        if parsed is None:
            return None
        keys.append(parsed.group("key"))
        if parsed.group("post") is not None:
            postnote = parsed.group("post").strip()
    # Biblatex attaches a single postnote to a lone key; drop it for multi-cites.
    if len(keys) == 1 and postnote is not None:
        return Autocite(keys[0], postnote=escape_latex(postnote))
    return Autocite(*keys)


def _inline_text(text: str) -> TeX:
    """Convert prose, turning Pandoc citations into cite nodes.

    Citation spans are pulled out first (so their keys are not LaTeX-escaped);
    the text around them keeps the euro/arrow/escape handling of :func:`_prose`.
    """
    parts: list[TeX] = []
    last = 0
    for match in CITATION_RE.finditer(text):
        node = _citation(match)
        if node is None:
            continue
        if match.start() > last:
            parts.append(_prose(text[last : match.start()]))
        parts.append(node)
        last = match.end()
    if not parts:
        return _prose(text)
    if last < len(text):
        parts.append(_prose(text[last:]))
    return Concat(*parts)


class MarkdownConverter:
    """Walk a marko AST, producing a single ``TeX`` tree.

    Subclass to add domain-specific blocks/inlines (see
    ``pytex_protocol.convert.ProtocolConverter``).
    """

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
            return _inline_text(text)

        if kind == "StrongEmphasis":
            return Bold(self.inlines(node))
        if kind == "Emphasis":
            return Emph(self.inlines(node))
        if kind in ("Link", "AutoLink", "Url"):
            dest = str(getattr(node, "dest", ""))
            if EXTERNAL_URL_RE.match(dest):
                return Href(dest, self.inlines(node))
            # Relative/local/anchor target: keep the text, drop the dead link.
            return self.inlines(node)
        if kind == "Image":
            dest = str(getattr(node, "dest", ""))
            if EXTERNAL_URL_RE.match(dest):
                return IncludeImage(dest)
            # The .tex is compiled in the build dir, not next to the Markdown
            # source, so a relative path would not resolve. Make it absolute
            # (relative to the CWD the build runs from) so \includegraphics
            # finds the file without copying or base64-embedding it.
            return IncludeImage(str(Path(dest).resolve()))
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
        idx = SECTION_INDEX + (level - 1) + self.base_level
        idx = max(0, min(idx, len(HEADINGS) - 1))
        return HEADINGS[idx](self.inlines(node))

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
        match = CALLOUT_RE.match(first_text)
        if match is None:
            return None
        box = CALLOUTS.get(match.group(1).upper())
        if box is None:
            return None
        # Rebuild the first paragraph with the marker stripped, keep the rest.
        stripped = first_text[match.end() :]
        head = Concat(
            _inline_text(stripped),
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
        # lstlisting with breaklines so long lines wrap instead of running off
        # the page. Language is intentionally omitted: listings aborts on
        # unknown languages, and Markdown info strings are unconstrained. The
        # body is bracketed by newlines because lstlisting reads code starting
        # on the line after \begin (and \end must sit on its own line).
        code = (text or "").rstrip("\n")
        return Lstlisting(f"\n{code}\n", {"breaklines": "true"})

    def _rule(self, _node: object) -> TeX:
        return Concat(Noindent(), Rule(r"\linewidth", "0.4pt"))

    def _table(self, node: object) -> TeX:
        """GFM pipe table -> ``tabularx`` (\\linewidth) with booktabs rules.

        The first ``TableRow`` is the header (separated by ``\\midrule``);
        per-column alignment comes from the cells' ``align`` attribute. ``X``
        columns wrap their content so wide tables stay inside the text width.
        """
        rows = [c for c in _children(node) if _kind(c) == "TableRow"]
        if not rows:
            return Empty
        head, *body = rows
        default = COLUMN_ALIGN[None]
        spec = "".join(
            COLUMN_ALIGN.get(cast("str | None", getattr(c, "align", None)), default)
            for c in _children(head)
            if _kind(c) == "TableCell"
        )
        body_rows = Concat(
            Raw("\n"),
            Toprule(),
            Raw("\n"),
            self._table_row(head),
            Midrule(),
            Raw("\n"),
            *(self._table_row(r) for r in body),
            Bottomrule(),
            Raw("\n"),
        )
        table = Tabularx(r"\linewidth", spec, body_rows)
        # Wrap in vertical space: `\par` closes the surrounding paragraph so
        # `\addvspace` lands in vertical mode both before and after the table.
        return Concat(
            Raw(f"\\par\\addvspace{{{TABLE_VSPACE}}}\n"),
            table,
            Raw(f"\n\\par\\addvspace{{{TABLE_VSPACE}}}"),
        )

    def _table_row(self, node: object) -> TeX:
        cells = [self.inlines(c) for c in _children(node) if _kind(c) == "TableCell"]
        # ``&`` between cells, ``\\`` after the last one. The genexp emits each
        # cell, prefixing every cell after the first with the column separator.
        return Concat(
            *(
                part
                for i, cell in enumerate(cells)
                for part in ((Raw(" & "), cell) if i else (cell,))
            ),
            Raw(" \\\\\n"),
        )

    def _eval_comment(self, node: object) -> TeX:
        """Evaluate a ``[//]: # "EXPR"`` Markdown comment as a pytex expression.

        This mirrors the ``\\iffalse{pytex(EXPR)}\\fi`` escape hatch in raw TeX:
        ``EXPR`` is evaluated with the Registry namespace. A ``TeX`` result is
        spliced into the tree as-is; anything else is stringified into ``Raw``.
        """
        title = getattr(node, "title", None)
        if not isinstance(title, str):
            return Empty
        expr = _strip_md_title(title)
        if not expr:
            return Empty
        result: Any = eval(expr, pytex_namespace())
        return result if isinstance(result, TeX) else Raw(str(result))

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
        if kind == "Table":
            return self._table(node)
        if kind == "LinkRefDef":
            # `[//]: # "EXPR"` is the Markdown-comment escape hatch: evaluate it.
            # Any other link reference definition renders to nothing.
            if (
                getattr(node, "label", None) == "//"
                and getattr(node, "dest", None) == "#"
            ):
                return self._eval_comment(node)
            return Empty
        if kind == "BlankLine":
            return Empty
        # Container we do not special-case (e.g. nested Document).
        kids = _children(node)
        return self.blocks(kids) if kids else Empty

    def blocks(self, nodes: list[object]) -> TeX:
        out = [self.block(n) for n in nodes if _kind(n) not in ("BlankLine",)]
        return Concat(*_interleave(out))


def _strip_md_title(title: str) -> str:
    """Strip the delimiters marko keeps around a link-ref-def title.

    Titles arrive quoted (``"..."``, ``'...'``) or parenthesised (``(...)``).
    """
    t = title.strip()
    if len(t) >= 2 and (
        (t[0] in "\"'" and t[-1] == t[0]) or (t[0] == "(" and t[-1] == ")")
    ):
        return t[1:-1].strip()
    return t


def _interleave(blocks: list[TeX]) -> Iterator[TeX]:
    """Yield non-empty block nodes separated by paragraph breaks."""
    kept = [b for b in blocks if b is not Empty]
    return (part for i, b in enumerate(kept) for part in ((PARBREAK, b) if i else (b,)))
