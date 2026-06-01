from typing import Protocol, Self, override, runtime_checkable

__all__ = ["PackageProtocol"]

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

    @property
    def parent(self) -> Self | None:
        """Parent node in the document tree, or None if root/detached."""
        return getattr(self, "_parent", None)

    @property
    def parents(self) -> tuple[Self, ...]:
        """Chain of ancestors from immediate parent up to root."""
        out: list[Self] = []
        cur = self.parent
        while cur is not None:
            out.append(cur)
            cur = cur.parent
        return tuple(out)

    @override
    def __str__(self) -> str:
        return self.rendered
