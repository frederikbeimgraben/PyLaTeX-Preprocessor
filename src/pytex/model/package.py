from typing import override

from pydantic.dataclasses import dataclass

_PACKAGES = dict[str, "Package"]()

type PackageOption = str | tuple[str, str]


@dataclass
class Package:
    name: str
    after: set["Package"]
    incompatible: set["Package"]
    options: set[PackageOption]

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
    def rendered(self) -> str:
        """Render this object to a valid LaTeX-String"""

        return f"\\usepackage{self._options_string}{{{self.name}}}"

    @property
    def children(self) -> None:
        return None

    @property
    def requires(self) -> set["Package"]:
        return self.after

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
        _PACKAGES[name].after |= after
        _PACKAGES[name].incompatible |= incompatible
        return _PACKAGES[name]

    return Package(
        name=name,
        after=after,
        incompatible=incompatible,
        options=options,
    )
