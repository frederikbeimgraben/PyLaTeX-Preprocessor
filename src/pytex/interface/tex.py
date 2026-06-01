from typing import Protocol, override, runtime_checkable

from .package import PackageProtocol

__all__ = ["TeX"]


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

    @property
    def parent(self) -> "TeX | None":
        """Parent node in the document tree, or None if root/detached."""
        return getattr(self, "_parent", None)

    @property
    def parents(self) -> tuple["TeX", ...]:
        """Chain of ancestors from immediate parent up to root."""
        out: list[TeX] = []
        cur = self.parent
        while cur is not None:
            out.append(cur)
            cur = cur.parent
        return tuple(out)

    @override
    def __str__(self) -> str:
        return self.rendered
