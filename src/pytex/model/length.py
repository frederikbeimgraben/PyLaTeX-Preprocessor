from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Final, override

from ..interface.tex import TeX
from ..registry import Registry

if TYPE_CHECKING:
    from ..interface.package import PackageProtocol

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
    `0.5 * Textwidth()`. `+`, `-` and `/` use the syntax of the calc package,
    so a `Length` built with one of them reports calc in `requires`. A plain
    `Length`, or one built only with `*` or unary `-`, needs no calc and
    reports no requirement.

    Pass a `Length` to anything that takes a length, for example `Vspace`,
    `Setlength`, or the width of a `Minipage`.
    """

    expr: Final[str]
    # True once `+`, `-` or `/` built this expression. `mul` and `neg` wrap
    # such an expression in parentheses, and `requires` reports calc for it.
    # `init=False` keeps this out of the constructor; the operators below
    # set it on the result with `object.__setattr__`, the same way a frozen
    # dataclass sets any field.
    _requires_calc: bool = field(default=False, init=False, compare=False, repr=False)

    @property
    @override
    def rendered(self) -> str:
        return self.expr

    @property
    @override
    def requires(self) -> "frozenset[PackageProtocol] | None":
        if not self._requires_calc:
            return None
        from ..packages import CALC

        return frozenset({CALC})

    def __add__(self, other: "Length | int | float | str") -> "Length":
        result = Length(f"{self.expr}+{_expr(other)}")
        object.__setattr__(result, "_requires_calc", True)
        return result

    def __radd__(self, other: "Length | int | float | str") -> "Length":
        result = Length(f"{_expr(other)}+{self.expr}")
        object.__setattr__(result, "_requires_calc", True)
        return result

    def __sub__(self, other: "Length | int | float | str") -> "Length":
        result = Length(f"{self.expr}-{_expr(other)}")
        object.__setattr__(result, "_requires_calc", True)
        return result

    def __rsub__(self, other: "Length | int | float | str") -> "Length":
        result = Length(f"{_expr(other)}-{self.expr}")
        object.__setattr__(result, "_requires_calc", True)
        return result

    def __mul__(self, factor: int | float) -> "Length":
        base = f"({self.expr})" if self._requires_calc else self.expr
        op = "*" if self._requires_calc else ""
        result = Length(f"{factor}{op}{base}")
        object.__setattr__(result, "_requires_calc", self._requires_calc)
        return result

    def __rmul__(self, factor: int | float) -> "Length":
        base = f"({self.expr})" if self._requires_calc else self.expr
        op = "*" if self._requires_calc else ""
        result = Length(f"{factor}{op}{base}")
        object.__setattr__(result, "_requires_calc", self._requires_calc)
        return result

    def __truediv__(self, divisor: int | float) -> "Length":
        base = f"({self.expr})" if self._requires_calc else self.expr
        result = Length(f"{base}/{divisor}")
        object.__setattr__(result, "_requires_calc", True)
        return result

    def __neg__(self) -> "Length":
        base = f"({self.expr})" if self._requires_calc else self.expr
        result = Length(f"-{base}")
        object.__setattr__(result, "_requires_calc", self._requires_calc)
        return result
