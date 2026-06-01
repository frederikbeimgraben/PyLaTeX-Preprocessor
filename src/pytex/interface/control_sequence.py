from typing import Protocol, runtime_checkable

from ..model.empty import EmptyTeX
from .tex import TeX

__all__ = ["ControlSequenceProtocol", "ParameterProtocol"]

type ParameterType = TeX | str | dict[str, str]


@runtime_checkable
class ParameterProtocol[T: ParameterType = ParameterType](TeX, Protocol):
    @property
    def optional(self) -> bool: ...

    @property
    def value(self) -> T: ...


type Parameters = tuple[ParameterProtocol | EmptyTeX, ...] | None


@runtime_checkable
class ControlSequenceProtocol[P: Parameters](TeX, Protocol):
    @property
    def name(self) -> str: ...

    @property
    def params(self) -> P: ...
