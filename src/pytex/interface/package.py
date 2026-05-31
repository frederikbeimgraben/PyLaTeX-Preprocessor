from typing import Protocol, Self, override, runtime_checkable

type PackageOption = str | tuple[str, str]


@runtime_checkable
class PackageProtocol(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def after(self) -> frozenset[Self]: ...

    @property
    def incompatible(self) -> frozenset[Self]: ...

    @property
    def options(self) -> frozenset[PackageOption]: ...

    @property
    def rendered(self) -> str:
        """Render this object to a valid LaTeX-String"""
        ...

    @property
    def children(self) -> tuple[Self, ...]:
        return ()

    @property
    def requires(self) -> frozenset[Self]:
        return self.after

    @override
    def __str__(self) -> str:
        return self.rendered
