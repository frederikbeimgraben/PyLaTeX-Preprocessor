"""Page watermark — diagonal repeated text built from native pytex.

The watermark text is supplied by the Python caller and baked into a
``\\DraftwatermarkOptions{...}`` invocation. No ``\\newcommand{\\waterMarkText}``,
no ``.tex`` asset.
"""

from dataclasses import dataclass
from typing import override

from pytex import BuiltinPackages, NewCounter, Package, TeX
from pytex_komascript.model import Block


@dataclass(init=False)
class DraftwatermarkOptions(TeX):
    """``\\DraftwatermarkOptions{key=val,...}`` from ``draftwatermark``."""

    scale: float
    angle: float
    color: str
    text: str

    def __init__(
        self,
        *,
        scale: float = 0.08,
        angle: float = 45,
        color: str = "black!12",
        text: str = "",
    ) -> None:
        self.scale = scale
        self.angle = angle
        self.color = color
        self.text = text

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return {BuiltinPackages.DRAFTWATERMARK.value}

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return (
            "\\DraftwatermarkOptions{"
            f"scale={self.scale},angle={self.angle},"
            f"text={{{_watermark_body(self.text)}}},"
            f"color={self.color}"
            "}"
        )


def _watermark_body(text: str) -> str:
    """The tabular/foreach body that tiles ``text`` across the page."""
    return (
        "\\begin{tabular}{c}%\n"
        "\\setcounter{it}{1}%\n"
        "\\whiledo{\\theit<100}{%\n"
        "\\foreach \\col in {0,...,15}{"
        f"\\color{{black!5}}\\BeginAccSupp{{ActualText=}}{text}~~"
        "\\EndAccSupp{}}\\\\%\n"
        "\\stepcounter{it}%\n"
        "}\n"
        "\\end{tabular}"
    )


def watermark_block(text: str = "") -> TeX:
    """Counter declaration + ``DraftwatermarkOptions`` with ``text`` baked in.

    When ``text`` is empty the options are still emitted so the package sees a
    well-formed configuration; just no visible glyphs end up on the page.
    """
    return Block(
        NewCounter("it"),
        DraftwatermarkOptions(text=text),
    )


__all__ = ["DraftwatermarkOptions", "watermark_block"]
