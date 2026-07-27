"""The interfaces for a LaTeX control sequence and for its parameters."""

from typing import Protocol, runtime_checkable

from ..model.empty import EmptyTeX
from .tex import TeX

__all__ = ["ControlSequenceProtocol", "ParameterProtocol"]

type ParameterType = TeX | str | dict[str, str]


@runtime_checkable
class ParameterProtocol[T: ParameterType = ParameterType](TeX, Protocol):
    """The interface for one parameter of a LaTeX control sequence.

    Attributes:
        optional: True when the parameter renders in square brackets. False
            when it renders in braces.
        value: The parameter content. A dictionary renders as a
            comma-separated list of `key=value` pairs.
    """

    @property
    def optional(self) -> bool: ...

    @property
    def value(self) -> T: ...


type Parameters = tuple[ParameterProtocol | EmptyTeX, ...] | None


@runtime_checkable
class ControlSequenceProtocol[P: Parameters](TeX, Protocol):
    """The interface for a LaTeX control sequence, for example `\\frac{a}{b}`.

    Attributes:
        name: The control sequence name without the leading backslash.
        params: The parameters in render order, or None for no parameters.
    """

    @property
    def name(self) -> str: ...

    @property
    def params(self) -> P: ...
