"""LaTeX math mode support."""

from dataclasses import dataclass
from typing import override

from .environments.standard import Environment
from ..model.base_model import TeX


@dataclass
class InlineMath(TeX):
    """Inline math: $content$"""

    content: TeX

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.content,)

    @override
    def serialize(self) -> str:
        return f"${self.content.serialize()}$"


@dataclass
class DisplayMath(TeX):
    r"""Display math: \[content\]"""

    content: TeX

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.content,)

    @override
    def serialize(self) -> str:
        return f"\\[\n{self.content.serialize()}\n\\]"


def Equation(content: TeX) -> Environment:
    """Numbered equation environment (requires amsmath)."""
    return Environment("equation", content)


def EquationStar(content: TeX) -> Environment:
    """Unnumbered equation environment (requires amsmath)."""
    return Environment("equation*", content)


def Align(content: TeX) -> Environment:
    """Multi-line aligned equations (requires amsmath)."""
    return Environment("align", content)


def AlignStar(content: TeX) -> Environment:
    """Multi-line aligned equations, no numbering (requires amsmath)."""
    return Environment("align*", content)


def Gather(content: TeX) -> Environment:
    """Centered multi-line equations (requires amsmath)."""
    return Environment("gather", content)
