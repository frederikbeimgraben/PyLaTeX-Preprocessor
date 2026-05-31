from typing import Protocol, runtime_checkable

from pytex.interface.tex import TeX

type ParameterType = TeX | str | dict[str, str]


@runtime_checkable
class ParameterProtocol[T: ParameterType = ParameterType](TeX, Protocol):
    @property
    def optional(self) -> bool: ...

    @property
    def value(self) -> T: ...


type Parameters = tuple[ParameterProtocol, ...] | None


@runtime_checkable
class ControlSequenceProtocol[P: Parameters](TeX, Protocol):
    @property
    def name(self) -> str: ...

    @property
    def params(self) -> P: ...
