"""Regression tests for the three high-severity backlog bugs in this cluster.

Each test reproduces one bug from `docs/bug-backlog.md` before the fix, then
guards the fix afterward.
"""

import marko

from pytex_markdown.protocol.convert import ProtocolConverter
from pytex_markdown.protocol.document import _PARSER
from pytex_markdown.protocol.shortcodes import expand_shortcode

_PLAIN_PARSER = marko.Markdown()

META: dict[str, object] = {}


def _render_md(md: str) -> str:
    converter = ProtocolConverter(meta=META)
    return converter.block(_PLAIN_PARSER.parse(md)).rendered


def test_vote_tally_reads_the_tally_line_not_the_whole_callout():
    # "Es gab ja 2 Nachfragen" is descriptive text, not the tally line.
    # `_is_tally_line` already excludes it from the box body, but `_tally`
    # searched the whole callout and matched "ja 2" there first.
    out = _render_md(
        "> [!abstimmung] Antrag\n"
        "> Es gab ja 2 Nachfragen\n"
        "> Ja: 12, Nein: 3, Enthaltung: 1"
    )
    assert r"\textbf{Ja:} 12" in out
    assert r"\textbf{Nein:} 3" in out
    assert r"\textbf{Enthaltung:} 1" in out
    assert r"\textbf{Ja:} 2" not in out


def test_protocol_parser_renders_gfm_tables():
    # `_PARSER` (used by `render_protocol`/`Protocol`/`IncludeProtocol`) must
    # parse the same GFM dialect as the top-level `pytex_markdown` parser, or
    # a pipe table degrades to a literal paragraph of pipes.
    md = "| a | b |\n|---|---|\n| 1 | 2 |\n"
    doc = _PARSER.parse(md)
    kinds = [type(child).__name__ for child in doc.children]
    assert kinds == ["Table"], (
        f"expected a GFM Table node, got {kinds}; the protocol parser is "
        "missing the gfm extension"
    )


def test_vote_shortcode_separator_has_no_missing_din_glyph():
    # U+00B7 (MIDDLE DOT) has no glyph in the bundled DIN font. The vote
    # summary must route it through `pytex_markdown.glyphs`, which rewrites
    # it to `\cdot`, instead of writing the bare character straight into the
    # rendered LaTeX.
    out = expand_shortcode("vote ja=12 nein=3 enthaltung=1", META).rendered
    assert "·" not in out
    assert r"\cdot" in out
