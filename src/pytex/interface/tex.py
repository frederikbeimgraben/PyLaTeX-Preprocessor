from typing import Protocol, override, runtime_checkable

from .package import Package


@runtime_checkable
class TeX(Protocol):
    @property
    def rendered(self) -> str:
        """Render this Node to a valid LaTeX-String"""
        ...

    @property
    def children(self) -> "TeX | None":
        """Children of the Node"""
        return None

    @property
    def requires(self) -> Package | None:
        return None

    @override
    def __str__(self) -> str:
        return self.rendered
