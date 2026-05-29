"""Font configuration — bundles ``tex/fonts.tex`` (fontspec fallback)."""

from pathlib import Path

from pytex import IncludeTeX, TeX

_TEX_DIR = Path(__file__).parent / "tex"


def fonts_block() -> TeX:
    """The fontspec fallback block (``tex/fonts.tex``)."""
    return IncludeTeX(_TEX_DIR / "fonts.tex")
