from typing import Protocol, override, runtime_checkable

from .package import PackageProtocol


@runtime_checkable
class TeX(Protocol):
    @property
    def rendered(self) -> str:
        """Render this Node to a valid LaTeX-String"""
        ...

    @property
    def children(self) -> tuple["TeX", ...]:
        """Children of the Node"""
        return ()

    @property
    def requires(self) -> frozenset[PackageProtocol] | None:
        return None

    @override
    def __str__(self) -> str:
        return self.rendered
