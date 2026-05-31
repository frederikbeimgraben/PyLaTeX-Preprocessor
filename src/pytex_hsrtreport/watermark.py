from typing import Final

from pytex.helpers.with_package import with_package
from pytex.interface.tex import TeX
from pytex.model.control_sequence import ControlSequence, Parameter
from pytex.model.package import DefinePackage
from pytex.model.raw import Raw
from pytex.packages import ACCSUPP, IFTHEN, PGFFOR, XCOLOR
from pytex.registry import Registry

DRAFTWATERMARK: Final = DefinePackage("draftwatermark")


def _watermark_text(text: str) -> str:
    """Build the tiled watermark grid: 100 rows × 16 cols, accessibility-friendly."""
    safe = text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
    return (
        r"\setcounter{it}{1}"
        + r"\whiledo{\theit<100}{"
        + r"\foreach \col in {0,...,15}{\color{black!5}\BeginAccSupp{ActualText=}"
        + f"{safe}~~"
        + r"\EndAccSupp{}}\\"
        + r"\stepcounter{it}}"
    )


@Registry.add
@with_package(DRAFTWATERMARK)
def DraftWatermark(
    text: str,
    scale: float = 0.08,
    angle: float = 45,
    color: str = "black!12",
) -> TeX:
    """Configure draftwatermark with tiled accessibility-safe text grid."""
    body = (
        f"scale={scale},angle={angle},"
        + f"text={{\\begin{{tabular}}{{c}}{_watermark_text(text)}\\end{{tabular}}}},"
        + f"color={color}"
    )
    return ControlSequence("DraftwatermarkOptions", (Parameter(Raw(body)),))


@Registry.add
def WatermarkCounter() -> TeX:
    """Declares the `it` counter used by DraftWatermark. Emit once in preamble."""
    return Raw("\\newcounter{it}")


@Registry.add
def WatermarkPackages() -> TeX:
    """Render `\\usepackage` lines for all packages required by watermark."""
    return ControlSequence(
        "RequirePackage",
        (Parameter("draftwatermark"),),
        required_packages=frozenset({IFTHEN, PGFFOR, ACCSUPP, XCOLOR, DRAFTWATERMARK}),
    )
