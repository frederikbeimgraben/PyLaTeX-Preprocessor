from importlib.resources import files
from pathlib import Path
from typing import Final

from pytex.commands.fontspec import Newfontfamily, Setmainfont, Setsansfont
from pytex.interface.tex import TeX
from pytex.model.concat import Concat
from pytex.model.raw import Raw
from pytex.registry import Registry

FONT_DIR: Final[Path] = Path(str(files("pytex_hsrtreport").joinpath("assets/fonts")))

# Output dir for the bundled TTFs, relative to the .tex file. `HSRTReport`'s
# `write_inline_fonts` copies the real font files here; fontspec's Path= option
# (see `_font_opts`) loads them from <this>/<subfamily>/.
FONT_OUTPUT_DIR: Final[str] = "fonts"


def all_font_paths() -> tuple[Path, ...]:
    """Return all bundled TTF paths, sorted for reproducible output."""
    return tuple(sorted(FONT_DIR.rglob("*.ttf")))


def rel(font_path: Path) -> str:
    """Path of a font file relative to `FONT_DIR`."""
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
    """fontspec setup for bundled DIN (main) and Blender (sans) fonts.

    Mirrors ``Config/Fonts.tex`` from the original template.  The font files
    are expected at ``fonts/DIN/`` and ``fonts/Blender/`` relative to the
    output ``.tex`` file, which is where ``HSRTReport.write_inline_fonts``
    copies the bundled TTFs before the TeX run.
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
