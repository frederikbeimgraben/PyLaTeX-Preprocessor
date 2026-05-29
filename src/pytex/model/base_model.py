from dataclasses import dataclass
from typing import Protocol, Self, runtime_checkable


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
