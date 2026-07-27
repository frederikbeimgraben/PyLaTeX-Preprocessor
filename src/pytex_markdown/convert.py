# pyright: reportAny=false, reportExplicitAny=false
"""Convert a marko parse tree into TeX nodes.

The converter maps a block element to a factory of the `pytex` library. A block
element is a heading, a list, a quote, a code block or a rule. The converter
maps an inline element to a text-formatting factory. A GitHub-style callout
(`> [!NOTE]` and the other markers) becomes a `pytex_components` colored box.
"""

from __future__ import annotations

import re
from itertools import groupby
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, cast

from pytex.commands.biblatex import Autocite, Textcite
from pytex.commands.builtin import (
    Bold,
    Chapter,
    Emph,
    Enumerate,
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
from .glyphs import glyph_node, is_special_char

__all__ = ["MarkdownConverter"]

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

# Heading commands, ordered from the broadest division downward. The default
# `base_level` of 0 maps a Markdown `#` (level 1) to `Section`.
HEADINGS: Final[tuple[Callable[..., TeX], ...]] = (
    Part,
    Chapter,
    Section,
    Subsection,
    Subsubsection,
    Paragraph,
    Subparagraph,
)
SECTION_INDEX: Final[int] = 2  # the position of Section in HEADINGS

CALLOUT_RE: Final[re.Pattern[str]] = re.compile(r"^\s*\[!(\w+)\]\s*", re.IGNORECASE)

# Only a link with a URL scheme (`https:`, `mailto:` and so on) or with a
# protocol-relative `//` stays a clickable `\href`. A relative or in-document
# target (`LICENSE`, `docs/x.md`, `#section`) points at a repository file that
# the PDF does not contain. hyperref would turn such a target into a dead
# `LICENSE.pdf` link, so the converter keeps the text and drops the URL.
EXTERNAL_URL_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?:[a-z][a-z0-9+.\-]*:|//)", re.IGNORECASE
)

# ASCII arrows in prose -> inline math arrows. Every target is a base-LaTeX
# macro, so no node requires an extra package. `<=` is absent on purpose. In
# prose it almost always means "less than or equal", not a left arrow.
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
# The longest alternatives come first, so `<-->` wins over `<-`.
ARROW_RE: Final[re.Pattern[str]] = re.compile(
    "|".join(re.escape(token) for token in sorted(ARROWS, key=len, reverse=True))
)
# The capturing variant makes `re.split` keep the matched arrows as the
# odd-indexed pieces. One pass then escapes the prose and substitutes the
# arrows.
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

# Pandoc-style citations in prose. A bracketed `[@key]`, `[@key, p. 5]` or
# `[@a; @b]` becomes `\autocite`. A narrative `@key` becomes `\textcite`. A
# narrative citation must not directly follow a word character or `@`, so an
# e-mail remnant like `foo@bar` never reads as a citation. An e-mail arrives as
# its own `Url` node anyway.
#
# A key uses the usual BibTeX character set. It starts with an alphanumeric
# character or an underscore, and it may hold internal punctuation. A key must
# not end on punctuation, so a trailing sentence period such as `@knuth.`
# stays outside the key. BibTeX keys cannot hold `#`, `$`, `%` or `&`, and
# each of those characters breaks a `\textcite`/`\autocite` argument when it
# reaches TeX unescaped, so the class excludes them. The character then stays
# in the surrounding prose, where `_prose` escapes it.
_CITE_KEY = r"[A-Za-z0-9_](?:[\w:.+?<>~/-]*[A-Za-z0-9_])?"
CITATION_RE: Final[re.Pattern[str]] = re.compile(
    r"\[(?P<bracket>\s*@[^\]]+)\]" + rf"|(?<![\w@])@(?P<narrative>{_CITE_KEY})"
)
_CITE_ENTRY_RE: Final[re.Pattern[str]] = re.compile(
    rf"^@(?P<key>{_CITE_KEY})\s*(?:,\s*(?P<post>.+))?$"
)

# listings has no escape mechanism for its own terminator. It closes the
# environment at the first line that starts with `\end{lstlisting}`, so a
# fenced code block that quotes that exact line would otherwise end the
# environment early and let the rest of the block run as live LaTeX.
_LSTLISTING_END_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?P<lead>[ \t]*)\\end\{lstlisting\}", re.MULTILINE
)

PARBREAK: Final[TeX] = Raw("\n\n")

# Vertical space above and below a rendered table. `\addvspace` (and not
# `\vspace`) merges with the adjacent spacing, so a table next to a heading or
# another block does not get a double gap.
TABLE_VSPACE: Final[str] = r"0.8\baselineskip"

# GFM cell alignment -> tabularx `X` column spec. `X` columns share the table
# width and wrap their content, so a wide table stays inside the text width.
# `None` (no colon) means left. Most Markdown converters treat an unaligned
# column the same way.
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
    """Return the literal text of a marko node.

    Returns:
        The text payload, or `None` when the node is a container.
    """
    ch = getattr(node, "children", None)
    return ch if isinstance(ch, str) else None


def _escape_text(text: str) -> str:
    """Escape prose for LaTeX and turn each ASCII arrow into a math arrow.

    The converter calls this for running text only, never for a code span or
    a code block. An arrow such as `->` becomes `$\\rightarrow$`. The function
    escapes the text around the arrow.

    `re.split` on the capturing group alternates prose and arrow. The odd
    pieces are the arrows. The even pieces are the text between them.
    """
    return "".join(
        f"${ARROWS[piece]}$" if index % 2 else escape_latex(piece)
        for index, piece in enumerate(ARROW_SPLIT_RE.split(text))
    )


def _prose(text: str) -> TeX:
    """Escape prose and give each special character its own node.

    The function groups the string into runs of ordinary text and runs of
    special characters. See `is_special_char`. An ordinary run keeps its arrow
    and escape handling inside a single `Raw` node.

    A mapped glyph (`€ → ↔ ≤ ≥ ·`) becomes its font-independent node. Any other
    special character becomes a `\\texttt{[missing glyph]}` placeholder plus a
    warning, because the DIN font has no glyph for it. One node per character
    keeps the spacing around it exact, so `50€` stays glyph-adjacent. See
    `pytex_markdown.glyphs`.
    """
    return Concat(
        *(
            node
            for special, group in groupby(text, is_special_char)
            for run in ("".join(group),)
            for node in (
                (glyph_node(ch) for ch in run)
                if special
                else ((Raw(_escape_text(run)),) if run else ())
            )
        )
    )


def _citation(match: re.Match[str]) -> TeX | None:
    """Build a cite node from a `CITATION_RE` match.

    A narrative `@key` becomes `\\textcite`. A bracketed `[@key]` becomes
    `\\autocite`. A single key may carry a postnote (`[@key, p. 5]`). One
    bracket may hold several keys (`[@a; @b]`).

    Returns:
        The cite node, or `None` when the bracket holds no valid `@key`. The
        caller then uses plain escaped text instead.
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
    # biblatex attaches a postnote to a lone key only. Drop it when the bracket
    # holds several keys.
    if len(keys) == 1 and postnote is not None:
        return Autocite(keys[0], postnote=escape_latex(postnote))
    return Autocite(*keys)


def _inline_text(text: str) -> TeX:
    """Convert prose and turn each Pandoc citation into a cite node.

    The function extracts the citation spans first, so LaTeX escaping never
    touches their keys. The text around them keeps the euro, arrow and escape
    handling of `_prose`.
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
    """Walk a marko parse tree and build one node tree.

    Subclass this class to add domain-specific blocks and inlines. See
    `pytex_markdown.protocol.convert.ProtocolConverter`.

    Attributes:
        base_level: The shift applied to the heading depth. The default `0`
            maps a Markdown `#` to `\\section`.
        callouts: When true, a `> [!NOTE]` block becomes a colored box.
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
            # A RawText, CodeSpan or Literal node carries a plain string.
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
            # A relative, local or in-document target has no live URL in the
            # PDF. Keep the text and drop the link.
            return self.inlines(node)
        if kind == "Image":
            dest = str(getattr(node, "dest", ""))
            if EXTERNAL_URL_RE.match(dest):
                return IncludeImage(dest)
            # tectonic compiles the rendered `.tex` file in the build
            # directory, not next to the Markdown input file, so a relative
            # path would not resolve. Make the path absolute against the
            # current working directory of the build. `\includegraphics` then
            # finds the file without a copy and without a base64 embed.
            return IncludeImage(str(Path(dest).resolve()))
        if kind == "LineBreak":
            soft = bool(getattr(node, "soft", False))
            return Raw(" ") if soft else Newline()

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
        # A tight item holds one paragraph. Inline its content so that the
        # item gets no extra break.
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
        stripped = first_text[match.end() :]
        head = Concat(
            _inline_text(stripped),
            *(self.inline(c) for c in inner[1:]),
        )
        body_blocks = [head, *(self.block(b) for b in kids[1:])]
        return box(Concat(*_interleave(body_blocks)))

    def _code(self, node: object) -> TeX:
        # marko puts the code text on the node itself for some block kinds and
        # inside one RawText child for the others. Read the direct text first,
        # then the child.
        text = _text(node)
        if text is None:
            kids = _children(node)
            text = _text(kids[0]) if kids else ""
        # `breaklines` wraps a long line. Without it a long line goes past the
        # page margin. The language is absent on purpose. listings stops with
        # an error on an unknown language, and a Markdown info string can hold
        # any word. `Lstlisting` brackets the body with its own newline, so
        # `_code` passes the bare text.
        code = (text or "").rstrip("\n")
        # Break a quoted `\end{lstlisting}` line so it cannot close the
        # environment early. The inserted space keeps the printed code
        # readable and stops the exact match that `listings` looks for.
        code = _LSTLISTING_END_RE.sub(r"\g<lead>\\end{ lstlisting}", code)
        return Lstlisting(code, {"breaklines": "true"})

    def _rule(self, _node: object) -> TeX:
        return Concat(Noindent(), Rule(r"\linewidth", "0.4pt"))

    def _table(self, node: object) -> TeX:
        """Convert a GFM pipe table to a `tabularx` with booktabs rules.

        The table spans `\\linewidth`. The first `TableRow` is the header, and
        `\\midrule` separates it from the body. The per-column alignment comes
        from the `align` attribute of the header cells. An `X` column wraps its
        content, so a wide table stays inside the text width.
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
        # `\par` closes the paragraph around the table, so `\addvspace` lands
        # in vertical mode both before and after the table.
        return Concat(
            Raw(f"\\par\\addvspace{{{TABLE_VSPACE}}}\n"),
            table,
            Raw(f"\n\\par\\addvspace{{{TABLE_VSPACE}}}"),
        )

    def _table_row(self, node: object) -> TeX:
        cells = [self.inlines(c) for c in _children(node) if _kind(c) == "TableCell"]
        return Concat(
            *(
                part
                for i, cell in enumerate(cells)
                for part in ((Raw(" & "), cell) if i else (cell,))
            ),
            Raw(" \\\\\n"),
        )

    def _eval_comment(self, node: object) -> TeX:
        """Evaluate a `[//]: # "EXPR"` Markdown comment as a pytex expression.

        This mirrors the inline `pytex(...)` marker of a `.tex` file. PyTeX
        evaluates `EXPR` with the Registry namespace. A `TeX` result goes into
        the node tree unchanged. Any other result becomes a `Raw` node that
        holds `str(result)`.

        **Warning:** this runs Python code from the Markdown input file. If
        the input file comes from a source you do not trust, do not convert it.
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
            # `[//]: # "EXPR"` is the Markdown counterpart of the inline
            # `pytex(...)` marker. Any other link reference definition
            # renders to nothing.
            if (
                getattr(node, "label", None) == "//"
                and getattr(node, "dest", None) == "#"
            ):
                return self._eval_comment(node)
            return Empty
        if kind == "BlankLine":
            return Empty
        # A container without a special case, for example a nested Document.
        kids = _children(node)
        return self.blocks(kids) if kids else Empty

    def blocks(self, nodes: list[object]) -> TeX:
        out = [self.block(n) for n in nodes if _kind(n) not in ("BlankLine",)]
        return Concat(*_interleave(out))


def _strip_md_title(title: str) -> str:
    """Strip the delimiters that marko keeps around a link-ref-def title.

    A title arrives in double quotes, in single quotes or in parentheses.
    """
    t = title.strip()
    if len(t) >= 2 and (
        (t[0] in "\"'" and t[-1] == t[0]) or (t[0] == "(" and t[-1] == ")")
    ):
        return t[1:-1].strip()
    return t


def _interleave(blocks: list[TeX]) -> Iterator[TeX]:
    """Yield the non-empty block nodes with a paragraph break between them."""
    kept = [b for b in blocks if b is not Empty]
    return (part for i, b in enumerate(kept) for part in ((PARBREAK, b) if i else (b,)))
