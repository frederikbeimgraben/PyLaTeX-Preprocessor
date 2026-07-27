"""Add a package requirement to a node or to a factory."""

from collections.abc import Callable
from dataclasses import dataclass, field
from functools import wraps
from typing import override

from pytex.interface.package import PackageProtocol

from ..interface.tex import TeX
from ..model.package import DefinePackage, Package
from ..registry import Registry
from .parenting import attach

__all__ = ["WithPackage", "coerce_package", "with_package"]


@Registry.add
def coerce_package(pkg: Package | str) -> Package:
    """Return a `Package` for `pkg`. A string value is a LaTeX package name."""
    if isinstance(pkg, Package):
        return pkg

    return DefinePackage(pkg)


@Registry.add
@dataclass
class WithPackage[T: TeX](TeX):
    """A node that adds one package requirement to the node tree.

    The node renders exactly what its child node renders. It only adds
    `package` to the package requirements that PyTeX collects for the
    preamble. A string value for `package` is a LaTeX package name.
    """

    child: T
    package: Package | str
    _parent: "TeX | None" = field(default=None, init=False, compare=False, repr=False)

    def __post_init__(self) -> None:
        attach(self, self.child)

    @property
    @override
    def rendered(self) -> str:
        return self.child.rendered

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.child,)

    @property
    @override
    def requires(self) -> frozenset[PackageProtocol] | None:
        return frozenset(
            {coerce_package(self.package)}
            | (self.child.requires or set[PackageProtocol]())
        )


def with_package[C: Callable[..., TeX]](pkg: Package | str) -> Callable[[C], C]:
    """Return a decorator that adds a package requirement to a factory.

    The decorated factory returns a `WithPackage` node that holds the node
    the original factory made. A string value for `pkg` is a LaTeX package
    name.
    """

    def decorator(func: C) -> C:
        @wraps(func)
        def wrapper(*args: object, **kwargs: object) -> TeX:
            return WithPackage(func(*args, **kwargs), pkg)

        return wrapper  # pyright: ignore[reportReturnType]

    return decorator
