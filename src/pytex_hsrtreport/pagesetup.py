from importlib.resources import files
from pathlib import Path
from typing import Final

from pytex.interface.tex import TeX
from pytex.model.include import IncludeTeX
from pytex.registry import Registry

__all__ = ["HSRTPageSetup"]

# The full preamble lives in tex/pagesetup.tex (too large to inline as a raw
# string); it is shipped as package data and loaded verbatim at render time.
SETUP_TEX: Final[Path] = Path(
    str(files("pytex_hsrtreport").joinpath("tex/pagesetup.tex"))
)


@Registry.add
def HSRTPageSetup() -> TeX:
    """KOMA scrheadings, section fonts, chapter-name tracking, typography.

    Mirrors ``Config/PageSetup.tex``, ``Config/Sections.tex``, and
    ``Config/Typography.tex`` from the original HSRTReport template.

    Must be emitted in the preamble *before* font setup: the ``\\providecommand``
    fallbacks here define ``\\blenderfont``/``\\dinfont`` as safe defaults, and
    ``HSRTFontSetup`` then overrides them with ``\\renewcommand`` once the real
    font families are declared.

    Defines ``\\ifHSRTBackMatter`` — set it to true in back matter to suppress
    chapter-specific headers/footers without calling mode-sensitive KOMA commands.
    """
    return IncludeTeX(SETUP_TEX, allow_replacements=False)
