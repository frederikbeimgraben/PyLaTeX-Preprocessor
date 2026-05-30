"""fontspec primitives: ``\\newfontfamily``, ``\\setmainfont``, ``\\setsansfont``.

The runtime ``\\IfFontExistsTF`` test lives in
:mod:`pytex.library.builtins.lowlevel`.
"""

from dataclasses import dataclass
from typing import override

from ..model.base_model import Package, TeX

_FONTSPEC: frozenset[Package | str] = frozenset({"fontspec"})


@dataclass
class NewFontFamily(TeX):
    """``\\newfontfamily\\name[opts]{family}``."""

    name: str
    family: str
    options: str | None = None

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return set(_FONTSPEC)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        opt = f"[{self.options}]" if self.options is not None else ""
        return f"\\newfontfamily\\{self.name}{opt}{{{self.family}}}"


@dataclass
class SetMainFont(TeX):
    """``\\setmainfont[opts]{family}``."""

    family: str
    options: str | None = None

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return set(_FONTSPEC)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        opt = f"[{self.options}]" if self.options is not None else ""
        return f"\\setmainfont{opt}{{{self.family}}}"


@dataclass
class SetSansFont(TeX):
    """``\\setsansfont[opts]{family}``."""

    family: str
    options: str | None = None

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return set(_FONTSPEC)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        opt = f"[{self.options}]" if self.options is not None else ""
        return f"\\setsansfont{opt}{{{self.family}}}"


@dataclass
class SetMonoFont(TeX):
    """``\\setmonofont[opts]{family}``."""

    family: str
    options: str | None = None

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return set(_FONTSPEC)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        opt = f"[{self.options}]" if self.options is not None else ""
        return f"\\setmonofont{opt}{{{self.family}}}"


__all__ = ["NewFontFamily", "SetMainFont", "SetSansFont", "SetMonoFont"]
