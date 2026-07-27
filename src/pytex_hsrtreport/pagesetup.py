"""Page setup for the HSRT report, loaded from a shipped `.tex` file."""

from importlib.resources import files
from pathlib import Path
from typing import Final

from pytex.interface.tex import TeX
from pytex.model.include import IncludeTeX
from pytex.registry import Registry

__all__ = ["HSRTPageSetup"]

# The full page setup lives in `tex/pagesetup.tex`. It is too large for a raw
# string in Python. The package ships it as package data, and PyTeX reads it
# verbatim at render time.
SETUP_TEX: Final[Path] = Path(
    str(files("pytex_hsrtreport").joinpath("tex/pagesetup.tex"))
)


@Registry.add
def HSRTPageSetup() -> TeX:
    r"""Set up the KOMA `scrheadings` style, the section fonts and typography.

    This node also tracks the current chapter name. It mirrors
    `Config/PageSetup.tex`, `Config/Sections.tex` and `Config/Typography.tex`
    from the original HSRT report template.

    Put this node in the preamble **before** the font setup. The
    `\providecommand` fallbacks here define `\blenderfont` and `\dinfont` as
    safe defaults. `HSRTFontSetup` then replaces both with `\renewcommand`
    after LaTeX declares the real font families.

    The node also defines `\ifHSRTBackMatter`. Set the flag to true in the
    back matter. LaTeX then leaves the chapter name out of the page header.
    With the flag you need none of the KOMA commands that depend on the
    current mode.
    The flag does not gate the page footer. The `Seite N von M` line (page N
    of M) stays on every numbered page.
    """
    return IncludeTeX(SETUP_TEX, allow_replacements=False)
