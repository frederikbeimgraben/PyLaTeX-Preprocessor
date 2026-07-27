"""Equivalence tests for the refactored helpers in `pytex_markdown.convert`.

A refactor replaced the accumulator loops with generator expressions and
comprehensions. Each test here compares the new output against a reference
implementation of the original loop over many inputs. A change in escaping,
order, or spacing makes a test fail.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast, override

import marko

from pytex.commands.builtin import Euro
from pytex.commands.tables import Bottomrule, Midrule, Tabularx, Toprule
from pytex.model.concat import Concat
from pytex.model.empty import Empty
from pytex.model.raw import Raw
from pytex_markdown.convert import (
    ARROW_RE,
    ARROWS,
    COLUMN_ALIGN,
    PARBREAK,
    TABLE_VSPACE,
    MarkdownConverter,
    _children,
    _escape_text,
    _interleave,
    _kind,
    _prose,
)
from pytex_markdown.escape import escape_latex

if TYPE_CHECKING:
    from pytex.interface.tex import TeX

PARSER = marko.Markdown(extensions=["gfm"])

# The euro sign drove the original `_prose`, and the reference implementation
# below still splits the text on it. The converter now holds the euro sign as
# the first entry of the glyph table. The old code stays here word for word.
EURO_SIGN = "€"

# These samples cover arrows, euro signs, adjacent glyphs, the string edges,
# and the LaTeX special characters.
PROSE_SAMPLES = [
    "",
    "plain text",
    "a -> b",
    "a <- b <-> c <=> d",
    "chain a --> b <-- c <--> d => e",
    "->leading and trailing<-",
    "-><-",  # two arrows with an empty gap between them
    "50€",
    "€ 50",
    "€€",  # two euro signs with an empty middle segment
    "€leading",
    "trailing€",
    "mix 5€ -> 10€ and a <=> b",
    r"specials: 100% & _ # $ {x} ~ ^ \ end",
    "umlauts äöü and €",
]


# -- reference implementations ---------------------------------------------


def _old_escape_text(text: str) -> str:
    out: list[str] = []
    last = 0
    for match in ARROW_RE.finditer(text):
        out.append(escape_latex(text[last : match.start()]))
        out.append(f"${ARROWS[match.group(0)]}$")
        last = match.end()
    out.append(escape_latex(text[last:]))
    return "".join(out)


def _old_prose(text: str) -> TeX:
    if EURO_SIGN not in text:
        return Raw(_escape_text(text))
    parts: list[TeX] = []
    for i, segment in enumerate(text.split(EURO_SIGN)):
        if i:
            parts.append(Euro())
        if segment:
            parts.append(Raw(_escape_text(segment)))
    return Concat(*parts)


def _old_interleave(blocks: list[TeX]) -> list[TeX]:
    kept = [b for b in blocks if b is not Empty]
    joined: list[TeX] = []
    for i, b in enumerate(kept):
        if i:
            joined.append(PARBREAK)
        joined.append(b)
    return joined


class _OldConverter(MarkdownConverter):
    """Converter that builds a table with the original loops."""

    @override
    def _table_row(self, node: object) -> TeX:
        cells = [self.inlines(c) for c in _children(node) if _kind(c) == "TableCell"]
        joined: list[TeX] = []
        for i, cell in enumerate(cells):
            if i:
                joined.append(Raw(" & "))
            joined.append(cell)
        joined.append(Raw(" \\\\\n"))
        return Concat(*joined)

    @override
    def _table(self, node: object) -> TeX:
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
        parts: list[TeX] = [Raw("\n"), Toprule(), Raw("\n"), self._table_row(head)]
        parts.append(Midrule())
        parts.append(Raw("\n"))
        parts.extend(self._table_row(r) for r in body)
        parts.append(Bottomrule())
        parts.append(Raw("\n"))
        table = Tabularx(r"\linewidth", spec, Concat(*parts))
        return Concat(
            Raw(f"\\par\\addvspace{{{TABLE_VSPACE}}}\n"),
            table,
            Raw(f"\n\\par\\addvspace{{{TABLE_VSPACE}}}"),
        )


# -- tests ------------------------------------------------------------------


def test_escape_text_matches_reference():
    for text in PROSE_SAMPLES:
        assert _escape_text(text) == _old_escape_text(text), text


def test_prose_matches_reference():
    for text in PROSE_SAMPLES:
        assert _prose(text).rendered == _old_prose(text).rendered, text


def test_interleave_matches_reference():
    blocks: list[TeX] = [Raw("a"), Empty, Raw("b"), Raw("c"), Empty]
    new = Concat(*_interleave(blocks)).rendered
    old = Concat(*_old_interleave(blocks)).rendered
    assert new == old
    # `_interleave` drops each `Empty` block. Exactly one parbreak separates
    # the blocks that stay.
    assert new == "a\n\nb\n\nc"


TABLES = [
    # a header row and two body rows, with a different alignment per column
    "| Name | Age | City |\n|:-----|:---:|-----:|\n"
    "| Bob | 30 | NYC |\n| Ann | 25 | LA |\n",
    # one column only
    "| Solo |\n|------|\n| one |\n",
    # cells that need LaTeX escaping
    "| a & b | 100% |\n|---|---|\n| _x_ | #1 |\n",
    # a header row and no body row
    "| H1 | H2 |\n|---|---|\n",
]


def test_table_rendering_matches_reference():
    for md in TABLES:
        ast = PARSER.parse(md)
        new = MarkdownConverter().block(ast).rendered
        old = _OldConverter().block(ast).rendered
        assert new == old, md
