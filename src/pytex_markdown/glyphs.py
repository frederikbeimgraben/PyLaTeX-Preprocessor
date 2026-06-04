# pyright: reportUnusedCallResult=false
"""Font-independent Unicode handling for Markdown prose.

tectonic compiles with XeTeX, which does *no* automatic font substitution: a
code point absent from the active text font silently renders as a blank "tofu"
box. The bundled DIN text font in particular lacks a handful of otherwise
common symbols (``€ → ↔ ≤ ≥ ·``). Rather than emit tofu we rewrite each such
code point to a font-independent construct via the data-driven :data:`GLYPH_NODES`
table -- either eurosym's ``\\euro{}`` (which ships its own glyph) or an
inline-math macro (rendered in the always-present math font), so the result no
longer depends on the text font at all.

A code point that is *neither* in the table *nor* present in every bundled DIN
weight is genuinely unrenderable: it is replaced by ``\\texttt{[missing glyph]}``
and a :class:`MissingGlyphWarning` is raised, so silent tofu never reaches the
PDF.

The DIN coverage check parses the fonts' ``cmap`` tables directly (no external
dependency). The rule is deliberately conservative: a code point counts as
renderable only if it is present in *every* bundled DIN weight, because a glyph
missing from a single weight (e.g. bold) would tofu wherever that weight is used.
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
    """Factory for an inline-math node wrapping a single base-LaTeX macro."""
    return lambda: InlineMath(Raw(macro))


# Unicode char -> font-independent node factory. The DIN text font lacks these
# glyphs, so the raw char would tofu; every target is font-independent -- eurosym
# ships its own euro glyph, and the math macros render in the math font. The
# arrow targets match the ASCII-arrow rewrites (``->`` -> ``\rightarrow`` etc.).
# ``·`` maps to ``\cdot`` (the math multiplication dot) rather than
# ``\textperiodcentered``: the latter is a *text*-font glyph and would itself
# tofu under DIN, whereas ``\cdot`` lives in the always-present math font.
GLYPH_NODES: Final[dict[str, Callable[[], TeX]]] = {
    "€": Euro,
    "→": _math(r"\rightarrow"),
    "↔": _math(r"\leftrightarrow"),
    "≤": _math(r"\leq"),
    "≥": _math(r"\geq"),
    "·": _math(r"\cdot"),
}

# Literal placeholder text emitted for a genuinely unrenderable character.
MISSING_GLYPH_TEXT: Final[str] = "[missing glyph]"


def glyph_node(ch: str) -> TeX:
    """Return the spliced node for a single special character.

    A character in :data:`GLYPH_NODES` becomes its font-independent node. Any
    other character reaching here is unrenderable: it becomes a
    ``\\texttt{[missing glyph]}`` placeholder and raises
    :class:`MissingGlyphWarning` (naming the char and its code point), so the
    loss is visible instead of a silent blank box.
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
    """True if ``ch`` must be spliced as its own node rather than kept in prose.

    A mapped glyph always splices. ASCII and whitespace always stay in prose
    (ASCII is fully covered by DIN, and LaTeX escaping handles the specials).
    Any other character splices only when DIN cannot render it -- in which case
    :func:`glyph_node` turns it into a ``[missing glyph]`` placeholder.
    """
    if ch in GLYPH_NODES:
        return True
    if ord(ch) < 0x80 or ch.isspace():
        return False
    return not renderable_in_din(ch)


def renderable_in_din(ch: str) -> bool:
    """True if ``ch`` has a glyph in *every* bundled DIN weight."""
    return ord(ch) in _din_codepoints()


# -- DIN cmap coverage -----------------------------------------------------


def _ints(fmt: str, data: bytes, offset: int) -> tuple[int, ...]:
    """``struct.unpack_from`` for an all-integer format, typed as ints.

    ``struct`` is stubbed as returning ``tuple[Any, ...]``; the cast pins the
    homogeneous integer results so the parsers stay statically typed.
    """
    return cast("tuple[int, ...]", struct.unpack_from(fmt, data, offset))


def _and(a: frozenset[int], b: frozenset[int]) -> frozenset[int]:
    return a & b


def _or(a: frozenset[int], b: frozenset[int]) -> frozenset[int]:
    return a | b


@lru_cache(maxsize=1)
def _din_codepoints() -> frozenset[int]:
    """Code points present in every bundled DIN weight (parsed once, cached)."""
    from pytex_hsrtreport.fonts import FONT_DIR

    weights = sorted((FONT_DIR / "DIN").glob("*.ttf"))
    if not weights:  # pragma: no cover - the fonts are bundled with the package
        return frozenset()
    # Conservative: a code point is renderable only if EVERY weight has it.
    return reduce(_and, (_font_codepoints(path) for path in weights))


def _table_offset(data: bytes, want: bytes) -> int | None:
    """Offset of the ``want`` table in the sfnt table directory, or ``None``.

    Each 16-byte record holds tag[0:4], checksum[4:8], offset[8:12], length.
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
    """All Unicode code points mapped to a non-zero glyph in a TrueType font."""
    data = path.read_bytes()
    cmap_off = _table_offset(data, b"cmap")
    if cmap_off is None:  # pragma: no cover - every text font has a cmap
        return frozenset()
    _version, sub_count = _ints(">HH", data, cmap_off)
    sub_offsets = {
        _ints(">HHI", data, cmap_off + 4 + 8 * i)[2] for i in range(sub_count)
    }
    # Union every Unicode subtable -- that is the coverage XeTeX sees.
    return reduce(
        _or,
        (_subtable_codepoints(data, cmap_off + off) for off in sub_offsets),
        frozenset[int](),
    )


def _subtable_codepoints(data: bytes, offset: int) -> frozenset[int]:
    """Code points of a single cmap subtable (formats 0, 4, 6, 12)."""
    (fmt,) = _ints(">H", data, offset)
    if fmt == 0:
        return _cmap_format0(data, offset)
    if fmt == 4:
        return _cmap_format4(data, offset)
    if fmt == 6:
        return _cmap_format6(data, offset)
    if fmt == 12:
        return _cmap_format12(data, offset)
    return frozenset()  # other formats are non-Unicode / legacy; ignore


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
    """Glyph id for ``code`` in segment ``i`` of a format-4 subtable."""
    if range_off[i] == 0:
        return (code + delta[i]) & 0xFFFF
    # idRangeOffset indexes forward from its own array slot into glyphIdArray.
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
