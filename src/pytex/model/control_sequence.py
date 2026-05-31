from dataclasses import dataclass, field
from typing import Final, Generic, TypeVar, override

from ..interface.control_sequence import Parameters, ParameterType
from ..interface.package import PackageProtocol
from ..interface.tex import TeX
from .raw import Raw

T = TypeVar("T", covariant=True, bound=ParameterType)


@dataclass(frozen=True, slots=True)
class Parameter(TeX, Generic[T]):
    value: Final[T]
    optional: Final[bool] = False

    @property
    def _braces(self) -> tuple[str, str]:
        return ("[", "]") if self.optional else ("{", "}")

    @property
    @override
    def children(self) -> tuple[TeX]:
        if isinstance(self.value, dict):
            return tuple[TeX]()

        return (self.value if isinstance(self.value, TeX) else Raw(self.value),)

    @property
    @override
    def rendered(self) -> str:
        """Render this Node to a valid LaTeX-String"""

        content: str | TeX = ""

        if isinstance(self.value, TeX) or isinstance(self.value, str):
            content = self.value
        else:
            content = ",".join(f"{key}={value}" for key, value in self.value.items())

        return f"{self._braces[0]}{content}{self._braces[1]}"


P = TypeVar("P", covariant=True, bound=Parameters)


@dataclass(frozen=True, slots=True)
class ControlSequence(TeX, Generic[P]):
    name: Final[str]
    params: Final[P]
    required_packages: frozenset[PackageProtocol] = field(default_factory=frozenset)

    @property
    @override
    def requires(self) -> frozenset[PackageProtocol]:
        return self.required_packages

    @property
    @override
    def rendered(self) -> str:
        return f"\\{self.name}{''.join(p.rendered for p in (self.params if self.params is not None else tuple()))}"
