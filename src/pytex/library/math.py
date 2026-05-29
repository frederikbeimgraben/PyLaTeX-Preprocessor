"""LaTeX math mode support."""

from dataclasses import dataclass
from typing import override

from ..model.base_model import TeX
from ..model.raw import coerce_tex
from .environments.standard import Environment


@dataclass(init=False)
class InlineMath(TeX):
    """Inline math: $content$"""

    content: TeX

    def __init__(self, content: TeX | str) -> None:
        self.content = coerce_tex(content)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.content,)

    @override
    def serialize(self) -> str:
        return f"${self.content.serialize()}$"


@dataclass(init=False)
class DisplayMath(TeX):
    r"""Display math: \[content\]"""

    content: TeX

    def __init__(self, content: TeX | str) -> None:
        self.content = coerce_tex(content)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.content,)

    @override
    def serialize(self) -> str:
        return f"\\[\n{self.content.serialize()}\n\\]"


def Equation(content: TeX | str) -> Environment:
    """Numbered equation environment (requires amsmath)."""
    return Environment("equation", content)


def EquationStar(content: TeX | str) -> Environment:
    """Unnumbered equation environment (requires amsmath)."""
    return Environment("equation*", content)


def Align(content: TeX | str) -> Environment:
    """Multi-line aligned equations (requires amsmath)."""
    return Environment("align", content)


def AlignStar(content: TeX | str) -> Environment:
    """Multi-line aligned equations, no numbering (requires amsmath)."""
    return Environment("align*", content)


def Gather(content: TeX | str) -> Environment:
    """Centered multi-line equations (requires amsmath)."""
    return Environment("gather", content)
