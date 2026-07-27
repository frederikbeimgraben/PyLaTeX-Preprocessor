"""fontspec setup for the bundled DIN and Blender font families."""

from importlib.resources import files
from pathlib import Path
from typing import Final

from pytex.commands.fontspec import Newfontfamily, Setmainfont, Setsansfont
from pytex.interface.tex import TeX
from pytex.model.concat import Concat
from pytex.model.raw import Raw
from pytex.registry import Registry

FONT_DIR: Final[Path] = Path(str(files("pytex_hsrtreport").joinpath("assets/fonts")))

# Directory for the bundled TTF files, relative to the rendered `.tex` file.
# `HSRTReport.write_inline_fonts` writes the font files to disk here. The
# fontspec `Path=` option in `_font_opts` loads them from
# `<this directory>/<subfamily>/`.
FONT_OUTPUT_DIR: Final[str] = "fonts"


def all_font_paths() -> tuple[Path, ...]:
    """Return the path of each bundled TTF file, in sorted order.

    The sort keeps the render reproducible.
    """
    return tuple(sorted(FONT_DIR.rglob("*.ttf")))


def rel(font_path: Path) -> str:
    """Return the path of a font file relative to `FONT_DIR`."""
    return font_path.relative_to(FONT_DIR).as_posix()


def _font_opts(subfamily: str, upright: str, italic: str) -> dict[str, str]:
    return {
        "Path": f"{FONT_OUTPUT_DIR}/{subfamily}/",
        "Extension": ".ttf",
        "UprightFont": upright,
        "BoldFont": "*-Bold",
        "ItalicFont": italic,
        "BoldItalicFont": "*-BoldItalic",
    }


@Registry.add
def HSRTFontSetup() -> TeX:
    """Set up fontspec for the bundled DIN (main) and Blender (sans) fonts.

    This node mirrors `Config/Fonts.tex` from the original template. LaTeX
    looks for the font files in `fonts/DIN/` and `fonts/Blender/`, relative
    to the rendered `.tex` file. `HSRTReport.write_inline_fonts` writes them
    to disk there before PyTeX compiles the document.
    """
    blender_opts = _font_opts("Blender", "*-Medium", "*-MediumItalic")
    din_opts = _font_opts("DIN", "*-Regular", "*-Italic")
    return Concat(
        Newfontfamily("\\BlenderFont", "Blender", options=blender_opts),
        Newfontfamily("\\DINFont", "DIN", options=din_opts),
        Raw(r"\renewcommand{\blenderfont}{\BlenderFont}"),
        Raw(r"\renewcommand{\dinfont}{\DINFont}"),
        Setsansfont("Blender", options=blender_opts),
        Setmainfont("DIN", options=din_opts),
    )


__all__ = [
    "FONT_OUTPUT_DIR",
    "HSRTFontSetup",
    "all_font_paths",
    "rel",
]
