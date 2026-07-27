# pyright: reportUnusedCallResult=false
"""Font-independent Unicode handling for Markdown prose.

tectonic compiles with XeTeX, and XeTeX does no automatic font substitution. A
code point that the active text font does not cover prints as a blank "tofu"
box, and nothing warns you. The bundled DIN text font lacks a few otherwise
common symbols (`€ → ↔ ≤ ≥ ·`). The `GLYPH_NODES` table rewrites each such code
point into a font-independent construct. A target is either the `\\euro{}`
macro of eurosym, which ships its own glyph, or an inline-math macro, which
uses the always-present math font. The result no longer depends on the text
font.

A code point that is neither in the table nor present in every bundled DIN
weight has no glyph at all. This module replaces it with
`\\texttt{[missing glyph]}` and issues a `MissingGlyphWarning`. Silent tofu
never reaches the PDF.

The DIN coverage check parses the `cmap` tables of the fonts directly, so it
needs no external dependency. The rule is conservative on purpose. A code point
counts as covered only when every bundled DIN weight has it. A glyph that one
weight (bold, for example) lacks would tofu in every place that uses that
weight.
"""

from __future__ import annotations

import struct
import warnings
from functools import lru_cache, reduce
from typing import TYPE_CHECKING, Final, cast

from pytex.commands.builtin import Euro, Texttt
from pytex.model.math import InlineMath
from pytex.model.raw import Raw

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from pytex.interface.tex import TeX

__all__ = [
    "GLYPH_NODES",
    "MISSING_GLYPH_TEXT",
    "MissingGlyphWarning",
    "glyph_node",
    "is_special_char",
    "renderable_in_din",
]


class MissingGlyphWarning(UserWarning):
    """A character has no DIN glyph and no font-independent mapping."""


def _math(macro: str) -> Callable[[], TeX]:
    """Return a factory for an inline-math node with one base-LaTeX macro."""
    return lambda: InlineMath(Raw(macro))


# Unicode character -> font-independent node factory. The DIN text font lacks
# these glyphs, so the bare character would tofu. eurosym ships its own euro
# glyph, and a math macro uses the math font. The arrow targets match the
# ASCII-arrow rewrites, so `->` and `→` both give `\rightarrow`.
#
# `·` maps to `\cdot`, the math multiplication dot, and not to
# `\textperiodcentered`. `\textperiodcentered` is a text-font glyph and would
# tofu under DIN. `\cdot` lives in the always-present math font.
GLYPH_NODES: Final[dict[str, Callable[[], TeX]]] = {
    "€": Euro,
    "→": _math(r"\rightarrow"),
    "↔": _math(r"\leftrightarrow"),
    "≤": _math(r"\leq"),
    "≥": _math(r"\geq"),
    "·": _math(r"\cdot"),
}

# The placeholder text that stands in for a character without a glyph.
MISSING_GLYPH_TEXT: Final[str] = "[missing glyph]"


def glyph_node(ch: str) -> TeX:
    """Return the node that stands for one special character.

    A character in `GLYPH_NODES` becomes its font-independent node. Any other
    character that reaches this function has no glyph. It becomes a
    `\\texttt{[missing glyph]}` placeholder. The function also issues a
    `MissingGlyphWarning` that names the character and its code point. You then
    see the loss instead of a silent blank box.
    """
    factory = GLYPH_NODES.get(ch)
    if factory is not None:
        return factory()
    warnings.warn(
        f"no glyph for {ch!r} (U+{ord(ch):04X}) in the bundled DIN font and no "
        + f"font-independent mapping; emitting {MISSING_GLYPH_TEXT!r} instead",
        MissingGlyphWarning,
        stacklevel=2,
    )
    return Texttt(Raw(MISSING_GLYPH_TEXT))


def is_special_char(ch: str) -> bool:
    """Test whether a character needs its own node instead of staying in prose.

    A mapped glyph always gets its own node. ASCII and whitespace always stay
    in prose. DIN covers ASCII in full, and LaTeX escaping handles the special
    characters. Any other character gets its own node only when DIN has no
    glyph for it. `glyph_node` then turns it into a `[missing glyph]`
    placeholder.
    """
    if ch in GLYPH_NODES:
        return True
    if ord(ch) < 0x80 or ch.isspace():
        return False
    return not renderable_in_din(ch)


def renderable_in_din(ch: str) -> bool:
    """Test whether every bundled DIN weight has a glyph for `ch`."""
    return ord(ch) in _din_codepoints()


# -- DIN cmap coverage -----------------------------------------------------


def _ints(fmt: str, data: bytes, offset: int) -> tuple[int, ...]:
    """Unpack an all-integer struct format and type the result as ints.

    The type stubs give `struct.unpack_from` a `tuple[Any, ...]` return type.
    The cast pins the homogeneous integer result, so the cmap parsers stay
    statically typed.
    """
    return cast("tuple[int, ...]", struct.unpack_from(fmt, data, offset))


def _and(a: frozenset[int], b: frozenset[int]) -> frozenset[int]:
    return a & b


def _or(a: frozenset[int], b: frozenset[int]) -> frozenset[int]:
    return a | b


@lru_cache(maxsize=1)
def _din_codepoints() -> frozenset[int]:
    """Return the code points that every bundled DIN weight covers."""
    from pytex_hsrtreport.fonts import FONT_DIR

    weights = sorted((FONT_DIR / "DIN").glob("*.ttf"))
    if not weights:  # pragma: no cover - the fonts are bundled with the package
        return frozenset()
    return reduce(_and, (_font_codepoints(path) for path in weights))


def _table_offset(data: bytes, want: bytes) -> int | None:
    """Return the offset of the `want` table in the sfnt table directory.

    Each 16-byte record holds tag[0:4], checksum[4:8], offset[8:12] and
    length[12:16].

    Returns:
        The offset in bytes, or `None` when the font has no such table.
    """
    (_sfnt, num_tables) = _ints(">IH", data, 0)
    return next(
        (
            _ints(">I", data, 20 + 16 * i)[0]
            for i in range(num_tables)
            if data[12 + 16 * i : 16 + 16 * i] == want
        ),
        None,
    )


def _font_codepoints(path: Path) -> frozenset[int]:
    """Return the code points that map to a non-zero glyph in a TrueType font."""
    data = path.read_bytes()
    cmap_off = _table_offset(data, b"cmap")
    if cmap_off is None:  # pragma: no cover - every text font has a cmap
        return frozenset()
    _version, sub_count = _ints(">HH", data, cmap_off)
    sub_offsets = {
        _ints(">HHI", data, cmap_off + 4 + 8 * i)[2] for i in range(sub_count)
    }
    # The union over every cmap subtable is the coverage that XeTeX sees. The
    # code does not filter on the platform ID, so a non-Unicode subtable also
    # contributes its codes.
    return reduce(
        _or,
        (_subtable_codepoints(data, cmap_off + off) for off in sub_offsets),
        frozenset[int](),
    )


def _subtable_codepoints(data: bytes, offset: int) -> frozenset[int]:
    """Return the code points of one cmap subtable of format 0, 4, 6 or 12."""
    (fmt,) = _ints(">H", data, offset)
    if fmt == 0:
        return _cmap_format0(data, offset)
    if fmt == 4:
        return _cmap_format4(data, offset)
    if fmt == 6:
        return _cmap_format6(data, offset)
    if fmt == 12:
        return _cmap_format12(data, offset)
    return frozenset()  # ignore the other formats: non-Unicode or deprecated


def _cmap_format0(data: bytes, offset: int) -> frozenset[int]:
    glyphs = _ints(">256B", data, offset + 6)
    return frozenset(code for code, glyph in enumerate(glyphs) if glyph != 0)


def _cmap_format4(data: bytes, offset: int) -> frozenset[int]:
    (seg_x2,) = _ints(">H", data, offset + 6)
    seg_count = seg_x2 // 2
    end = _ints(f">{seg_count}H", data, offset + 14)
    start_off = offset + 14 + seg_x2 + 2  # + reservedPad
    start = _ints(f">{seg_count}H", data, start_off)
    delta = _ints(f">{seg_count}h", data, start_off + seg_x2)
    range_off_pos = start_off + 2 * seg_x2
    range_off = _ints(f">{seg_count}H", data, range_off_pos)
    return frozenset(
        code
        for i in range(seg_count)
        if start[i] != 0xFFFF
        for code in range(start[i], end[i] + 1)
        if _format4_glyph(data, i, code, start, delta, range_off, range_off_pos) != 0
    )


def _format4_glyph(
    data: bytes,
    i: int,
    code: int,
    start: tuple[int, ...],
    delta: tuple[int, ...],
    range_off: tuple[int, ...],
    range_off_pos: int,
) -> int:
    """Return the glyph id for `code` in segment `i` of a format-4 subtable."""
    if range_off[i] == 0:
        return (code + delta[i]) & 0xFFFF
    # idRangeOffset counts forward from its own array slot into glyphIdArray.
    glyph_pos = range_off_pos + 2 * i + range_off[i] + 2 * (code - start[i])
    if glyph_pos + 2 > len(data):
        return 0
    (glyph,) = _ints(">H", data, glyph_pos)
    return 0 if glyph == 0 else (glyph + delta[i]) & 0xFFFF


def _cmap_format6(data: bytes, offset: int) -> frozenset[int]:
    first, count = _ints(">HH", data, offset + 6)
    glyphs = _ints(f">{count}H", data, offset + 10)
    return frozenset(first + index for index, glyph in enumerate(glyphs) if glyph != 0)


def _cmap_format12(data: bytes, offset: int) -> frozenset[int]:
    (n_groups,) = _ints(">I", data, offset + 12)
    groups = (_ints(">III", data, offset + 16 + 12 * i) for i in range(n_groups))
    return frozenset(
        code
        for start_code, end_code, _start_glyph in groups
        for code in range(start_code, end_code + 1)
    )
