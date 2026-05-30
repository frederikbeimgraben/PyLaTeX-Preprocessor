"""glossaries-package style and key declarations.

Bare commands for defining custom glossary styles, column types and extra
entry keys (``\\newcolumntype``, ``\\newglossarystyle``, ``\\setglossarystyle``,
``\\glsaddkey``).
"""

from dataclasses import dataclass
from typing import override

from ..model.base_model import Package, TeX

_GLOSSARIES: frozenset[Package | str] = frozenset({"glossaries"})
_ARRAY: frozenset[Package | str] = frozenset({"array"})


def _coerce(value: TeX | str) -> TeX:
    from ..model.raw import Raw

    if isinstance(value, TeX):
        return value
    return Raw(value, escape_spaces=False)


@dataclass(init=False)
class NewColumnType(TeX):
    """``\\newcolumntype{name}[n]{body}`` from ``array``."""

    name: str
    body: TeX
    n_args: int

    def __init__(self, name: str, body: TeX | str, *, n_args: int = 0) -> None:
        self.name = name
        self.body = _coerce(body)
        self.n_args = n_args

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return set(_ARRAY)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.body,)

    @override
    def serialize(self) -> str:
        arity = f"[{self.n_args}]" if self.n_args else ""
        return f"\\newcolumntype{{{self.name}}}{arity}{{{self.body.serialize()}}}"


@dataclass(init=False)
class NewGlossaryStyle(TeX):
    """``\\newglossarystyle{name}{body}``."""

    name: str
    body: TeX

    def __init__(self, name: str, body: TeX | str) -> None:
        self.name = name
        self.body = _coerce(body)

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return set(_GLOSSARIES)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.body,)

    @override
    def serialize(self) -> str:
        return f"\\newglossarystyle{{{self.name}}}{{{self.body.serialize()}}}"


@dataclass
class SetGlossaryStyle(TeX):
    """``\\setglossarystyle{name}``."""

    name: str

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return set(_GLOSSARIES)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return f"\\setglossarystyle{{{self.name}}}"


@dataclass
class GlsAddKey(TeX):
    """``\\glsaddkey{key}{default}{\\\\glsentry...}{\\\\Glsentry...}{\\\\gls...}{\\\\Gls...}{\\\\GLS...}``."""

    key: str
    default: str
    entry: str
    entry_upper: str
    cs: str
    cs_upper: str
    cs_all: str

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return set(_GLOSSARIES)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return (
            f"\\glsaddkey{{{self.key}}}{{{self.default}}}"
            f"{{\\{self.entry}}}{{\\{self.entry_upper}}}"
            f"{{\\{self.cs}}}{{\\{self.cs_upper}}}{{\\{self.cs_all}}}"
        )


__all__ = [
    "NewColumnType",
    "NewGlossaryStyle",
    "SetGlossaryStyle",
    "GlsAddKey",
]
