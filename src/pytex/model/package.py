from logging import Logger
from typing import Self, override

from ..interface.package import PackageProtocol
from ..interface.tex import TeX
from ..registry import Registry

__all__ = ["DefinePackage", "Package"]

PACKAGES = dict[str, "Package"]()

type PackageOption = str | tuple[str, str]


@Registry.add
class Package(PackageProtocol, TeX):
    _name: str
    _after: set[Self]
    _incompatible: set[Self]
    _options: set[PackageOption]

    def __init__(
        self,
        name: str,
        after: set[Self] | frozenset[Self] | None = None,
        incompatible: set[Self] | frozenset[Self] | None = None,
        options: set[PackageOption] | frozenset[PackageOption] | None = None,
    ) -> None:
        self._name, self._after, self._incompatible, self._options = (
            name,
            set(after or set()),
            set(incompatible or set()),
            set(options or set()),
        )

    @property
    @override
    def name(self) -> str:
        return self._name

    @property
    @override
    def after(self) -> frozenset[Self]:
        return frozenset(self._after)

    @property
    @override
    def incompatible(self) -> frozenset[Self]:
        return frozenset(self._incompatible)

    @property
    @override
    def options(self) -> frozenset[PackageOption]:
        return frozenset(self._options)

    def amend(
        self,
        after: set[Self] | frozenset[Self] | None = None,
        incompatible: set[Self] | frozenset[Self] | None = None,
    ) -> None:
        if after is not None:
            self._after |= after
        if incompatible is not None:
            self._incompatible |= incompatible

    def __post_init__(self) -> None:
        if self.name not in PACKAGES:
            PACKAGES[self.name] = self
        else:
            Logger(self.__class__.__name__).warning(
                f"Multiple Instances of {self.name} in circulation!"
            )

    @property
    def _options_string(self) -> str:
        return (
            f"[{
                ','.join(
                    item if isinstance(item, str) else f'{item[0]}={item[1]}'
                    for item in self.options
                )
            }]"
            if len(self.options) != 0
            else ""
        )

    @property
    @override
    def rendered(self) -> str:
        return f"\\usepackage{self._options_string}{{{self.name}}}"

    @property
    @override
    def children(self) -> tuple[Self, ...]:
        return ()

    @property
    @override
    def requires(self) -> frozenset[Self]:
        return frozenset(self.after)

    @override
    def __str__(self) -> str:
        return self.rendered


@Registry.add
def DefinePackage(
    name: str,
    after: set[Package] | None = None,
    incompatible: set[Package] | None = None,
    options: set[PackageOption] | None = None,
) -> Package:
    after, incompatible, options = (
        after or set(),
        incompatible or set(),
        options or set(),
    )
    if name in PACKAGES:
        PACKAGES[name].amend(after=after, incompatible=incompatible)
        return PACKAGES[name]

    pkg = Package(
        name=name,
        after=after,
        incompatible=incompatible,
        options=options,
    )
    PACKAGES[name] = pkg
    return pkg
