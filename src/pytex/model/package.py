from typing import Self, override

from ..interface.package import PackageProtocol
from ..interface.tex import TeX

_PACKAGES = dict[str, "Package"]()

type PackageOption = str | tuple[str, str]


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
    ):
        self._name, self._after, self._incompatible, self._options = (
            name,
            set(*(after or set())),
            set(*(incompatible or set())),
            set(*(options or set())),
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
    ):
        if after is not None:
            self._after |= after
        if incompatible is not None:
            self._incompatible |= incompatible

    def __post_init__(self) -> None:
        if self.name not in _PACKAGES:
            _PACKAGES[self.name] = self

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
        """Render this object to a valid LaTeX-String"""

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
    if name in _PACKAGES:
        _PACKAGES[name].amend(after=after, incompatible=incompatible)
        return _PACKAGES[name]

    return Package(
        name=name,
        after=after,
        incompatible=incompatible,
        options=options,
    )
