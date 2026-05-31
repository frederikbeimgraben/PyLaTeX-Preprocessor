from typing import Protocol, override

type PackageOption = str | tuple[str, str]


class Package(Protocol):
    name: str
    after: set["Package"]
    incompatible: set["Package"]
    options: set[PackageOption]

    @property
    def rendered(self) -> str:
        """Render this object to a valid LaTeX-String"""
        ...

    @property
    def children(self) -> None:
        return None

    @property
    def requires(self) -> set["Package"]:
        return self.after

    @override
    def __str__(self) -> str:
        return self.rendered
