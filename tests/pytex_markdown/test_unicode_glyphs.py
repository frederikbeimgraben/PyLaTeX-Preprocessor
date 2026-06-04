"""Font-independent Unicode handling in Markdown prose.

Covers the data-driven glyph table (``€ → ↔ ≤ ≥ ·``), the ``[missing glyph]``
fallback + warning for a char the DIN font cannot render, and that code spans
stay verbatim. The euro path is the first table entry; its dedicated regression
suite lives in ``test_euro.py``.
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

# char -> the LaTeX fragment its node must render to.
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
    # No mapped source char survives into the output.
    assert not any(ch in out for ch in MAPPED)


def test_arrow_targets_match_ascii_arrows():
    # The `→` / `↔` entries reuse the existing ASCII-arrow macros, so the unicode
    # and ASCII spellings produce identical math.
    assert r"$\rightarrow$" in Markdown("a → b").rendered
    assert r"$\rightarrow$" in Markdown("a -> b").rendered
    assert r"$\leftrightarrow$" in Markdown("a ↔ b").rendered


def test_spacing_preserved_around_mapped_char():
    # Glued stays glued; spaced keeps its space (per-char splice, no run merge).
    assert r"50\euro{}" in Markdown("50€").rendered
    assert r"\euro{} 50" in Markdown("€ 50").rendered


def test_unrenderable_char_becomes_placeholder_and_warns():
    # U+4E2D is absent from DIN and unmapped -> placeholder + a warning.
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
    # German diacritics are in every DIN weight: escaped as text, no placeholder.
    with warnings.catch_warnings():
        warnings.simplefilter("error", MissingGlyphWarning)
        out = Markdown("Grüße über Lösungen").rendered
    assert "Grüße über Lösungen" in out
    assert MISSING_GLYPH_TEXT not in out


def test_mapped_char_untouched_in_code_span():
    # Code spans render verbatim; no rewrite, no warning.
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
    # ASCII and German text render; the mapped/unknown symbols do not.
    assert renderable_in_din("A")
    assert renderable_in_din("ä")
    assert not renderable_in_din("€")
    assert not renderable_in_din("中")


def test_ascii_and_whitespace_never_special():
    assert not any(is_special_char(ch) for ch in "Hello, world! 123\n\t")
    assert is_special_char("€")
    assert is_special_char("中")
