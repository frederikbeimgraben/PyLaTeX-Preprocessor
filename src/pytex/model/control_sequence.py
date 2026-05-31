from typing import Final, Generic, TypeVar, override

from pydantic.dataclasses import dataclass

from pytex.interface.control_sequence import Parameters
from pytex.interface.tex import TeX
from pytex.model.raw import Raw

T = TypeVar("T", covariant=True, bound=TeX | str)


@dataclass(frozen=True, slots=True)
class Parameter(TeX, Generic[T]):
    value: Final[T]
    optional: Final[bool] = False

    @property
    def _braces(self) -> tuple[str, str]:
        return ("[", "]") if self.optional else ("{", "}")

    @property
    @override
    def rendered(self) -> str:
        """Render this Node to a valid LaTeX-String"""

        return f"{self._braces[0]}{self.value.rendered if isinstance(self.value, TeX) else Raw(self.value)}{self._braces[1]}"


P = TypeVar("P", covariant=True, bound=Parameters)


@dataclass(frozen=True, slots=True)
class ControlSequence(TeX, Generic[P]):
    name: Final[str]
    params: Final[P]

    @property
    @override
    def rendered(self) -> str:
        return f"\\{self.name}{''.join(p.rendered for p in (self.params if self.params is not None else tuple()))}"
