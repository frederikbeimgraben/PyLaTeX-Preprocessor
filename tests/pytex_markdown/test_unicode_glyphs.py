"""Font-independent Unicode handling in Markdown prose.

The Markdown converter maps the characters `€ → ↔ ≤ ≥ ·` through the glyph
table. For a character that the DIN font cannot render, the converter writes
the `[missing glyph]` text and warns. A code span stays verbatim.

The euro sign is the first table entry. Its own tests live in `test_euro.py`.
"""

from __future__ import annotations

import warnings

import pytest

from pytex_markdown import Markdown
from pytex_markdown.glyphs import (
    MISSING_GLYPH_TEXT,
    MissingGlyphWarning,
    is_special_char,
    renderable_in_din,
)

# character -> the LaTeX fragment that its TeX node must render to.
MAPPED = {
    "€": r"\euro{}",
    "→": r"$\rightarrow$",
    "↔": r"$\leftrightarrow$",
    "≤": r"$\leq$",
    "≥": r"$\geq$",
    "·": r"$\cdot$",
}


@pytest.mark.parametrize(("char", "target"), MAPPED.items())
def test_mapped_char_becomes_font_independent_node(char: str, target: str):
    out = Markdown(f"a {char} b").rendered
    assert target in out
    assert char not in out


def test_all_mapped_chars_in_one_run():
    out = Markdown("€ → ↔ ≤ ≥ ·").rendered
    for target in MAPPED.values():
        assert target in out
    assert not any(ch in out for ch in MAPPED)


def test_arrow_targets_match_ascii_arrows():
    # The `→` and `↔` entries use the same macros as the ASCII arrows, so both
    # spellings give the same math.
    assert r"$\rightarrow$" in Markdown("a → b").rendered
    assert r"$\rightarrow$" in Markdown("a -> b").rendered
    assert r"$\leftrightarrow$" in Markdown("a ↔ b").rendered


def test_spacing_preserved_around_mapped_char():
    # The converter makes one node per character and does not merge runs.
    # A space next to the character stays, and no new space appears.
    assert r"50\euro{}" in Markdown("50€").rendered
    assert r"\euro{} 50" in Markdown("€ 50").rendered


def test_unrenderable_char_becomes_placeholder_and_warns():
    # The DIN font has no U+4E2D, and the glyph table has no entry for it.
    with pytest.warns(MissingGlyphWarning, match=r"U\+4E2D"):
        out = Markdown("price 中 tag").rendered
    assert rf"\texttt{{{MISSING_GLYPH_TEXT}}}" in out
    assert "中" not in out


def test_missing_glyph_warning_names_the_char():
    with pytest.warns(MissingGlyphWarning) as record:
        _ = Markdown("✓ done").rendered
    message = str(record[0].message)
    assert "✓" in message
    assert "U+2713" in message


def test_renderable_char_left_as_text():
    # Every DIN weight has the German diacritics, so the converter keeps them
    # as escaped text.
    with warnings.catch_warnings():
        warnings.simplefilter("error", MissingGlyphWarning)
        out = Markdown("Grüße über Lösungen").rendered
    assert "Grüße über Lösungen" in out
    assert MISSING_GLYPH_TEXT not in out


def test_mapped_char_untouched_in_code_span():
    # A code span renders verbatim. The converter does not rewrite it and
    # does not warn.
    out = Markdown("`a → b ≤ €`").rendered
    assert r"\texttt{a → b ≤ €}" in out
    assert r"$\rightarrow$" not in out
    assert r"\euro{}" not in out


def test_unrenderable_char_untouched_in_code_span():
    with warnings.catch_warnings():
        warnings.simplefilter("error", MissingGlyphWarning)
        out = Markdown("`中`").rendered
    assert r"\texttt{中}" in out
    assert MISSING_GLYPH_TEXT not in out


# -- classification helpers ------------------------------------------------


def test_din_renderability_is_conservative():
    # The DIN font renders ASCII and German text. It renders neither a mapped
    # symbol nor an unknown symbol.
    assert renderable_in_din("A")
    assert renderable_in_din("ä")
    assert not renderable_in_din("€")
    assert not renderable_in_din("中")


def test_ascii_and_whitespace_never_special():
    assert not any(is_special_char(ch) for ch in "Hello, world! 123\n\t")
    assert is_special_char("€")
    assert is_special_char("中")
