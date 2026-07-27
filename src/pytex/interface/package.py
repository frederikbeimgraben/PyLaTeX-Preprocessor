"""The interface for a LaTeX package that a TeX node can require."""

from typing import Protocol, Self, override, runtime_checkable

__all__ = ["PackageProtocol"]

type PackageOption = str | tuple[str, str]


@runtime_checkable
class PackageProtocol(Protocol):
    """The interface that a LaTeX package definition implements.

    A node requires a package through this interface. PyTeX collects the
    package requirements of the node tree and assembles the preamble from
    them.

    Attributes:
        name: The LaTeX package name, without the `.sty` extension.
        after: The packages that LaTeX must load before this package.
        incompatible: The packages that LaTeX must not load with this one.
        options: The package options. A string is a flag. A pair of strings
            is a key and its value, which render as `key=value`.
    """

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
        """The LaTeX source that loads this package with its options."""
        ...

    @property
    def children(self) -> tuple[Self, ...]:
        """The child nodes of a package. A package is always a leaf."""
        return ()

    @property
    def requires(self) -> frozenset[Self]:
        """The package requirements of this package. They are the `after` set."""
        return self.after

    @property
    def parent(self) -> Self | None:
        """The parent node. A package that no node holds returns None."""
        return getattr(self, "_parent", None)

    @property
    def parents(self) -> tuple[Self, ...]:
        """The parent nodes, from the direct parent node up to the root node."""
        out: list[Self] = []
        cur = self.parent
        while cur is not None:
            out.append(cur)
            cur = cur.parent
        return tuple(out)

    @override
    def __str__(self) -> str:
        return self.rendered
