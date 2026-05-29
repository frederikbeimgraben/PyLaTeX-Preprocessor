from dataclasses import dataclass
from typing import Protocol, Self, cast, override, runtime_checkable


@dataclass
class Package:
    name: str
    conflicts: set[Self | str]
    requires: set[Self | str]


@runtime_checkable
class TeX(Protocol):
    @property
    def required_packages(self) -> set[Package | str]:
        return set()

    @property
    def children(self) -> tuple["TeX", ...]: ...

    def serialize(self) -> str: ...


def WithPackage[T: TeX](model: type[T], *packages: Package | str) -> type[T]:
    class wrapped(model, Protocol):
        @property
        @override
        def required_packages(self) -> set[Package | str]:
            return super().required_packages.union(set(packages))

    return cast(type[T], wrapped)
