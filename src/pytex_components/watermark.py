from typing import Final

from pytex.helpers.with_package import with_package
from pytex.interface.tex import TeX
from pytex.model.control_sequence import ControlSequence, Parameter
from pytex.model.package import DefinePackage
from pytex.model.raw import Raw
from pytex.packages import ACCSUPP, IFTHEN, PGFFOR, XCOLOR
from pytex.registry import Registry

__all__ = ["DraftWatermark", "WatermarkCounter", "WatermarkPackages"]

DRAFTWATERMARK: Final = DefinePackage("draftwatermark")


def _watermark_text(text: str) -> str:
    """Build the tiled watermark grid of 99 rows and 16 columns.

    Each cell wraps the text in `\\BeginAccSupp{ActualText=}`, so a screen
    reader skips the watermark.

    The function escapes a brace in `text`. It also doubles a backslash. LaTeX
    reads a double backslash inside the `tabular` as a new row. If `text` holds
    a backslash, the grid breaks. Do not put a backslash in `text`.
    """
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
@with_package(IFTHEN)
@with_package(PGFFOR)
@with_package(ACCSUPP)
@with_package(XCOLOR)
def DraftWatermark(
    text: str,
    scale: float = 0.08,
    angle: float = 45,
    color: str = "black!12",
) -> TeX:
    """Set the draftwatermark options to a tiled grid of `text`.

    Args:
        text: The watermark text. Do not put a backslash in `text`. LaTeX
            reads the escaped backslash as a new row of the grid.
        angle: The rotation of the watermark in degrees.
        color: An xcolor color name, for example `black!12`.

    Note:
        The grid needs the counter `it`. Put `WatermarkCounter` in the
        preamble before you use this factory.
    """
    body = (
        f"scale={scale},angle={angle},"
        + f"text={{\\begin{{tabular}}{{c}}{_watermark_text(text)}\\end{{tabular}}}},"
        + f"color={color}"
    )
    return ControlSequence("DraftwatermarkOptions", (Parameter(Raw(body)),))


@Registry.add
def WatermarkCounter() -> TeX:
    """Declare the counter `it` that `DraftWatermark` uses.

    Put the result in the preamble one time only. A second `\\newcounter{it}`
    is a LaTeX error.
    """
    return Raw("\\newcounter{it}")


@Registry.add
def WatermarkPackages() -> TeX:
    """Require every package that the draft watermark needs.

    The node renders `\\RequirePackage{draftwatermark}` and names the other
    watermark packages as package requirements, so the preamble loads them.
    """
    return ControlSequence(
        "RequirePackage",
        (Parameter("draftwatermark"),),
        required_packages=frozenset({IFTHEN, PGFFOR, ACCSUPP, XCOLOR, DRAFTWATERMARK}),
    )
