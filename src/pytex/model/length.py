from dataclasses import dataclass
from typing import Final, override

from ..interface.tex import TeX
from ..registry import Registry

__all__ = ["Length"]


def _expr(value: "Length | int | float | str") -> str:
    if isinstance(value, Length):
        return value.expr
    return str(value)


@Registry.add
@dataclass(frozen=True)
class Length(TeX):
    """A LaTeX length expression, for example `\\textwidth` or `0.5\\textwidth`.

    The Python operators build the arithmetic: `Linewidth() - "0.5cm"` or
    `0.5 * Textwidth()`. The arithmetic uses the syntax of the calc package, so
    the document must load calc. `Length` does not require calc on its own.

    Pass a `Length` to anything that takes a length, for example `Vspace`,
    `Setlength`, or the width of a `Minipage`.
    """

    expr: Final[str]

    @property
    @override
    def rendered(self) -> str:
        return self.expr

    def __add__(self, other: "Length | int | float | str") -> "Length":
        return Length(f"{self.expr}+{_expr(other)}")

    def __radd__(self, other: "Length | int | float | str") -> "Length":
        return Length(f"{_expr(other)}+{self.expr}")

    def __sub__(self, other: "Length | int | float | str") -> "Length":
        return Length(f"{self.expr}-{_expr(other)}")

    def __rsub__(self, other: "Length | int | float | str") -> "Length":
        return Length(f"{_expr(other)}-{self.expr}")

    def __mul__(self, factor: int | float) -> "Length":
        return Length(f"{factor}{self.expr}")

    def __rmul__(self, factor: int | float) -> "Length":
        return Length(f"{factor}{self.expr}")

    def __truediv__(self, divisor: int | float) -> "Length":
        return Length(f"{self.expr}/{divisor}")

    def __neg__(self) -> "Length":
        return Length(f"-{self.expr}")
