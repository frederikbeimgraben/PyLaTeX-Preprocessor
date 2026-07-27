"""The interface that every TeX node in a node tree implements."""

from typing import Protocol, override, runtime_checkable

from .package import PackageProtocol

__all__ = ["TeX"]


@runtime_checkable
class TeX(Protocol):
    """The interface that every TeX node implements.

    A node renders itself and its child nodes, and it names its own package
    requirements. PyTeX walks the node tree through `children` and assembles
    the preamble from the `requires` sets it finds.
    """

    @property
    def rendered(self) -> str:
        """The LaTeX source for this TeX node and for its child nodes."""
        ...

    @property
    def children(self) -> tuple["TeX", ...]:
        """The child nodes of this TeX node. A node with no child node is a leaf."""
        return ()

    @property
    def requires(self) -> frozenset[PackageProtocol] | None:
        """The package requirements of this node, or None when it has none."""
        return None

    @property
    def parent(self) -> "TeX | None":
        """The parent node. The root node returns None.

        A node that no parent node holds yet also returns None.
        """
        return getattr(self, "_parent", None)

    @property
    def parents(self) -> tuple["TeX", ...]:
        """The parent nodes, from the direct parent node up to the root node."""
        out: list[TeX] = []
        cur = self.parent
        while cur is not None:
            out.append(cur)
            cur = cur.parent
        return tuple(out)

    @override
    def __str__(self) -> str:
        return self.rendered
