import base64
from dataclasses import dataclass, field
from importlib.resources import files
from pathlib import Path
from typing import Final, override

from pytex.commands.fontspec import Newfontfamily, Setmainfont, Setsansfont
from pytex.interface.tex import TeX
from pytex.model.concat import Concat
from pytex.registry import Registry

_FONT_DIR: Final[Path] = Path(str(files("pytex_hsrtreport").joinpath("assets/fonts")))

# Output path prefix used in filecontents* targets and fontspec Path= options.
# Fonts are decoded to <this>/<subfamily>/ relative to the .tex file.
FONT_OUTPUT_DIR: Final[str] = "fonts"


def all_font_paths() -> tuple[Path, ...]:
    """Return all bundled TTF paths, sorted for reproducible output."""
    return tuple(sorted(_FONT_DIR.rglob("*.ttf")))


def rel(font_path: Path) -> str:
    """Path of a font file relative to `_FONT_DIR`."""
    return font_path.relative_to(_FONT_DIR).as_posix()


def filecontents_font_b64_block(font_path: Path) -> str:
    """Emit a `\\filecontents*` block that writes `<rel>.b64` during TeX compilation."""
    payload = base64.b64encode(font_path.read_bytes()).decode("ascii")
    chunks = [payload[i : i + 76] for i in range(0, len(payload), 76)]
    body = "\n".join(chunks)
    target = f"{FONT_OUTPUT_DIR}/{rel(font_path)}.b64"
    return (
        f"\\begin{{filecontents*}}[overwrite,nosearch]{{{target}}}\n"
        f"{body}\n"
        "\\end{filecontents*}\n"
    )


@Registry.add
@dataclass
class HSRTInlineFonts(TeX):
    """Emit `\\filecontents*` base64 blocks for every bundled HSRT font TTF."""

    _parent: "TeX | None" = field(default=None, init=False, compare=False, repr=False)

    @property
    @override
    def rendered(self) -> str:
        return "\n".join(filecontents_font_b64_block(p) for p in all_font_paths())


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
    output ``.tex`` file, which is where the build helper decodes the
    ``filecontents*`` base64 blobs written by `HSRTInlineFonts`.
    """
    blender_opts = _font_opts("Blender", "*-Medium", "*-MediumItalic")
    din_opts = _font_opts("DIN", "*-Regular", "*-Italic")
    return Concat(
        Newfontfamily("\\BlenderFont", "Blender", options=blender_opts),
        Newfontfamily("\\DINFont", "DIN", options=din_opts),
        Setsansfont("Blender", options=blender_opts),
        Setmainfont("DIN", options=din_opts),
    )


__all__ = [
    "FONT_OUTPUT_DIR",
    "HSRTFontSetup",
    "HSRTInlineFonts",
    "filecontents_font_b64_block",
]
