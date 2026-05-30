"""TikZ environments and global helpers.

:class:`TikzPicture` wraps ``\\begin{tikzpicture}[opts] ... \\end{tikzpicture}``.
:class:`Scope` does the same for ``scope``. :class:`UseTikzLibrary` and
:class:`TikzSet` are the two preamble-time configuration commands.
"""

from dataclasses import dataclass
from typing import override

from pytex import Package, TeX
from pytex.model.raw import coerce_tex
from pytex_komascript.model import Block


@dataclass(init=False)
class TikzPicture(TeX):
    """``\\begin{tikzpicture}[opts] body \\end{tikzpicture}`` environment."""

    body: TeX
    options: str | None

    def __init__(
        self,
        *body: TeX | str,
        options: str | None = None,
    ) -> None:
        coerced = tuple(coerce_tex(b) for b in body)
        self.body = (
            coerced[0] if len(coerced) == 1 else Block(*coerced)
        )
        self.options = options

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return {"tikz"}

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.body,)

    @override
    def serialize(self) -> str:
        opt = f"[{self.options}]" if self.options is not None else ""
        return (
            f"\\begin{{tikzpicture}}{opt}\n"
            f"{self.body.serialize()}\n"
            f"\\end{{tikzpicture}}"
        )


@dataclass(init=False)
class Scope(TeX):
    """``\\begin{scope}[opts] body \\end{scope}`` environment."""

    body: TeX
    options: str | None

    def __init__(
        self,
        *body: TeX | str,
        options: str | None = None,
    ) -> None:
        coerced = tuple(coerce_tex(b) for b in body)
        self.body = (
            coerced[0] if len(coerced) == 1 else Block(*coerced)
        )
        self.options = options

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return {"tikz"}

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.body,)

    @override
    def serialize(self) -> str:
        opt = f"[{self.options}]" if self.options is not None else ""
        return (
            f"\\begin{{scope}}{opt}\n"
            f"{self.body.serialize()}\n"
            f"\\end{{scope}}"
        )


@dataclass
class TikzSet(TeX):
    """``\\tikzset{key=value, ...}`` — set tikz styles globally / scope-locally."""

    options: str

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return {"tikz"}

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return f"\\tikzset{{{self.options}}}"


@dataclass
class UseTikzLibrary(TeX):
    """``\\usetikzlibrary{lib1,lib2,...}`` — load tikz libraries (preamble)."""

    libraries: tuple[str, ...]

    def __init__(self, *libraries: str) -> None:
        object.__setattr__(self, "libraries", tuple(libraries))

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return {"tikz"}

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return f"\\usetikzlibrary{{{','.join(self.libraries)}}}"


@dataclass
class PgfMathSetMacro(TeX):
    """``\\pgfmathsetmacro{\\name}{expr}`` — bind a pgfmath result to a macro."""

    name: str
    expression: str

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return {"tikz"}

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return f"\\pgfmathsetmacro{{\\{self.name}}}{{{self.expression}}}"


__all__ = [
    "TikzPicture",
    "Scope",
    "TikzSet",
    "UseTikzLibrary",
    "PgfMathSetMacro",
]
