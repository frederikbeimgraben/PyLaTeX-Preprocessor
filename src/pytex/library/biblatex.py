"""biblatex primitives needed to configure cite-formatting and bib-output.

Bare commands (``\\ExecuteBibliographyOptions``, ``\\DeclareFieldFormat``,
``\\DeclareCiteCommand``, ``\\DeclareNameAlias``, ``\\addbibresource``,
``\\printbibliography``) used in custom citation setups. The package itself is
added to the document's package list separately so options live in one place.
"""

from dataclasses import dataclass
from typing import override

from ..model.base_model import Package, TeX
from ..model.raw import coerce_tex

_BIBLATEX: frozenset[Package | str] = frozenset({"biblatex"})


def _coerce(value: TeX | str) -> TeX:
    from ..model.raw import Raw

    if isinstance(value, TeX):
        return value
    return Raw(value, escape_spaces=False)


@dataclass
class ExecuteBibliographyOptions(TeX):
    """``\\ExecuteBibliographyOptions{key=val,...}``."""

    options: str

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return set(_BIBLATEX)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return f"\\ExecuteBibliographyOptions{{{self.options}}}"


@dataclass(init=False)
class DeclareFieldFormat(TeX):
    """``\\DeclareFieldFormat{name}{body}`` — formats a bib field."""

    name: str
    body: TeX

    def __init__(self, name: str, body: TeX | str) -> None:
        self.name = name
        self.body = _coerce(body)

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return set(_BIBLATEX)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.body,)

    @override
    def serialize(self) -> str:
        return f"\\DeclareFieldFormat{{{self.name}}}{{{self.body.serialize()}}}"


@dataclass(init=False)
class DeclareCiteCommand(TeX):
    """``\\DeclareCiteCommand{\\cite}[wrapper]{init}{loop}{sep}{final}``."""

    name: str
    wrapper: str | None
    init: TeX
    loop: TeX
    sep: TeX
    final: TeX

    def __init__(
        self,
        name: str,
        init: TeX | str,
        loop: TeX | str,
        sep: TeX | str,
        final: TeX | str,
        *,
        wrapper: str | None = None,
    ) -> None:
        self.name = name
        self.wrapper = wrapper
        self.init = _coerce(init)
        self.loop = _coerce(loop)
        self.sep = _coerce(sep)
        self.final = _coerce(final)

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return set(_BIBLATEX)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.init, self.loop, self.sep, self.final)

    @override
    def serialize(self) -> str:
        wrap = f"[{self.wrapper}]" if self.wrapper is not None else ""
        return (
            f"\\DeclareCiteCommand{{\\{self.name}}}{wrap}"
            f"{{{self.init.serialize()}}}"
            f"{{{self.loop.serialize()}}}"
            f"{{{self.sep.serialize()}}}"
            f"{{{self.final.serialize()}}}"
        )


@dataclass
class DeclareNameAlias(TeX):
    """``\\DeclareNameAlias{alias}{target}``."""

    alias: str
    target: str

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return set(_BIBLATEX)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return f"\\DeclareNameAlias{{{self.alias}}}{{{self.target}}}"


@dataclass
class AddBibResource(TeX):
    """``\\addbibresource{path}``."""

    path: str

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return set(_BIBLATEX)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return f"\\addbibresource{{{self.path}}}"


@dataclass
class PrintBibliography(TeX):
    """``\\printbibliography[heading=...,title=...]``."""

    heading: str | None = None
    title: str | None = None

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return set(_BIBLATEX)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        opts: list[str] = []
        if self.heading is not None:
            opts.append(f"heading={self.heading}")
        if self.title is not None:
            opts.append(f"title={{{self.title}}}")
        opt_str = f"[{','.join(opts)}]" if opts else ""
        return f"\\printbibliography{opt_str}"


__all__ = [
    "ExecuteBibliographyOptions",
    "DeclareFieldFormat",
    "DeclareCiteCommand",
    "DeclareNameAlias",
    "AddBibResource",
    "PrintBibliography",
]
