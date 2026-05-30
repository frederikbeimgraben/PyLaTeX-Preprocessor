"""TikZ environments and global helpers.

:class:`TikzPicture` wraps ``\\begin{tikzpicture}[opts] ... \\end{tikzpicture}``.
:class:`Scope` does the same for ``scope``. Both accept only legal tikz
content — :class:`Node`, :class:`CoordinateNode`, :class:`Path`, nested
:class:`Scope`, :class:`TikzSet`, :class:`PgfMathSetMacro` and the
build-time loop helper :class:`ForEach` — so passing a stray ``Section`` or
``Raw`` text is caught at construction.

:class:`UseTikzLibrary` and :class:`TikzSet` are the two preamble-time
configuration commands.
"""

from dataclasses import dataclass
from typing import override

from pytex import Package, TeX
from pytex_komascript.model import Block

from .foreach import ForEach
from .node import CoordinateNode, Node
from .path import Path

#: Anything legal inside a tikzpicture / scope body.
type TikzContent = Node | CoordinateNode | Path | "Scope" | "TikzSet" | "PgfMathSetMacro" | "ForEach"


def _coerce_tikz_block(parts: "tuple[TikzContent, ...]") -> TeX:
    """Pack tikz content into a Block; reject non-tikz nodes."""
    for p in parts:
        if not isinstance(
            p, (Node, CoordinateNode, Path, Scope, TikzSet, PgfMathSetMacro, ForEach)
        ):
            raise TypeError(
                f"tikzpicture body cannot contain {type(p).__name__}; "
                "only Node, CoordinateNode, Path, Scope, TikzSet, "
                "PgfMathSetMacro and ForEach are allowed."
            )
    return parts[0] if len(parts) == 1 else Block(*parts)


@dataclass(init=False)
class TikzPicture(TeX):
    """``\\begin{tikzpicture}[opts] body \\end{tikzpicture}`` environment.

    Accepts only tikz primitives (:data:`TikzContent`). To embed arbitrary
    text inside the picture, place it in a :class:`Node`.
    """

    body: TeX
    options: str | None

    def __init__(
        self,
        *body: TikzContent,
        options: str | None = None,
    ) -> None:
        self.body = _coerce_tikz_block(body)
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
    """``\\begin{scope}[opts] body \\end{scope}`` — same content rules as
    :class:`TikzPicture`."""

    body: TeX
    options: str | None

    def __init__(
        self,
        *body: TikzContent,
        options: str | None = None,
    ) -> None:
        self.body = _coerce_tikz_block(body)
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
    "TikzContent",
]
