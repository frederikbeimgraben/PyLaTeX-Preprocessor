from typing import Protocol

from pytex.interface.tex import TeX


class ParameterProtocol[T: TeX | str](TeX, Protocol):
    @property
    def optional(self) -> bool: ...

    @property
    def value(self) -> T: ...


type Parameters = tuple[ParameterProtocol[TeX], ...] | None


class ControlSequenceProtocol[P: Parameters](TeX, Protocol):
    @property
    def name(self) -> str: ...

    @property
    def params(self) -> P: ...
