from collections.abc import Callable
from dataclasses import dataclass, field
from functools import wraps
from typing import override

from pytex.interface.package import PackageProtocol

from ..interface.tex import TeX
from ..model.package import Package
from ..registry import Registry
from .parenting import attach

__all__ = ["WithPackage", "coerce_package", "with_package"]


@Registry.add
def coerce_package(pkg: Package | str) -> Package:
    if isinstance(pkg, Package):
        return pkg

    return Package(pkg)


@Registry.add
@dataclass
class WithPackage[T: TeX](TeX):
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
    def decorator(func: C) -> C:
        @wraps(func)
        def wrapper(*args: object, **kwargs: object) -> TeX:
            return WithPackage(func(*args, **kwargs), pkg)

        return wrapper  # pyright: ignore[reportReturnType]

    return decorator
