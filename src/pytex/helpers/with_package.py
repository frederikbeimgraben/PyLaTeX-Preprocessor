# pyright: reportAny=false, reportExplicitAny=false
from dataclasses import dataclass
from typing import Any, Callable, override

from ..interface.tex import TeX
from ..model.package import Package


def coerce_package(pkg: Package | str) -> Package:
    if isinstance(pkg, Package):
        return pkg

    return Package(pkg)


@dataclass
class WithPackage[T: TeX](TeX):
    child: T
    package: Package | str

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
    def requires(self) -> frozenset[Package] | None:
        return frozenset({coerce_package(self.package)})


def with_package[C: Callable[..., TeX]](pkg: Package | str) -> Callable[[C], C]:
    def decorator(func: C) -> C:
        def wrapper(*args: Any, **kwargs: Any) -> TeX:
            return WithPackage(func(*args, **kwargs), pkg)

        return wrapper  # pyright: ignore[reportReturnType]

    return decorator
