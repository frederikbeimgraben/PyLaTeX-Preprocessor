"""Box-style environments: ``minipage``, ``picture`` / ``\\put``, ``mdframed``.

These are LaTeX environments rather than primitives so a typed wrapper
keeps the ``\\begin``/``\\end`` pair balanced and surfaces required packages.
"""

from dataclasses import dataclass
from typing import override

from ...model.base_model import Package, TeX
from ...model.raw import Raw
from ..environments.standard import Environment


def _coerce_body(value: TeX | str) -> TeX:
    """Coerce a body to TeX without space-escaping internal spaces.

    Environment / box bodies are TeX source — internal spaces must survive
    as actual whitespace, not as ``~`` ties.
    """
    if isinstance(value, TeX):
        return value
    return Raw(value, escape_spaces=False)


def _body(parts: "tuple[TeX | str, ...]") -> TeX:
    from ...model.group import Group

    if len(parts) == 1:
        return _coerce_body(parts[0])
    return Group(*(_coerce_body(p) for p in parts))


@dataclass(init=False)
class Minipage(TeX):
    """``\\begin{minipage}[pos]{width} body \\end{minipage}``."""

    width: str
    body: TeX
    position: str | None

    def __init__(
        self,
        width: str,
        *body: TeX | str,
        position: str | None = None,
    ) -> None:
        self.width = width
        self.position = position
        self.body = _body(body)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.body,)

    @override
    def serialize(self) -> str:
        pos = f"[{self.position}]" if self.position is not None else ""
        return (
            f"\\begin{{minipage}}{pos}{{{self.width}}}"
            f"{self.body.serialize()}"
            f"\\end{{minipage}}"
        )


@dataclass(frozen=True)
class Put:
    """``\\put(x,y){body}`` — picture-environment placement.

    Not a standalone TeX node: only meaningful as a member of :class:`Picture`.
    """

    x: str
    y: str
    body: TeX

    def serialize(self) -> str:
        return f"\\put({self.x},{self.y}){{{self.body.serialize()}}}"


@dataclass(init=False)
class Picture(TeX):
    """``\\begin{picture}(w,h)(x0,y0) ...\\put... \\end{picture}``.

    A ``picture`` environment only takes ``\\put`` operations (plus
    decorations) — accepting arbitrary TeX would be a typing lie. Children
    are :class:`Put` instances.
    """

    width: str
    height: str
    offset: tuple[str, str] | None
    ops: tuple[Put, ...]

    def __init__(
        self,
        *ops: Put,
        width: str,
        height: str,
        offset: tuple[str, str] | None = None,
    ) -> None:
        self.width = width
        self.height = height
        self.offset = offset
        self.ops = tuple(ops)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return tuple(op.body for op in self.ops)

    @override
    def serialize(self) -> str:
        off = f"({self.offset[0]},{self.offset[1]})" if self.offset is not None else ""
        body = "\n".join(op.serialize() for op in self.ops)
        return (
            f"\\begin{{picture}}({self.width},{self.height}){off}\n"
            f"{body}\n\\end{{picture}}"
        )


_MDFRAMED: frozenset[Package | str] = frozenset({"mdframed"})


@dataclass(init=False)
class MDFramed(TeX):
    """``\\begin{mdframed}[opts] body \\end{mdframed}`` (mdframed)."""

    body: TeX
    options: str | None

    def __init__(self, *body: TeX | str, options: str | None = None) -> None:
        self.body = _body(body)
        self.options = options

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return set(_MDFRAMED)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.body,)

    @override
    def serialize(self) -> str:
        opt = f"[{self.options}]" if self.options is not None else ""
        return (
            f"\\begin{{mdframed}}{opt}\n"
            f"{self.body.serialize()}\n"
            f"\\end{{mdframed}}"
        )


_LONGTABLE: frozenset[Package | str] = frozenset({"longtable"})


@dataclass(init=False)
class LongTable(TeX):
    """``\\begin{longtable}{cols} body \\end{longtable}`` (longtable)."""

    columns: str
    body: TeX

    def __init__(self, columns: str, *body: TeX | str) -> None:
        self.columns = columns
        self.body = _body(body)

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return set(_LONGTABLE)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.body,)

    @override
    def serialize(self) -> str:
        return (
            f"\\begin{{longtable}}{{{self.columns}}}\n"
            f"{self.body.serialize()}\n"
            f"\\end{{longtable}}"
        )


@dataclass(init=False)
class TabularEnv(TeX):
    """``\\begin{tabular}{cols} body \\end{tabular}`` with arbitrary body.

    Unlike :class:`pytex.library.figures.tables.Tabular`, which builds the
    rows itself, ``TabularEnv`` accepts any TeX body. Use it when the body
    is produced by another TeX macro (e.g. ``\\the\\titlePageData``).
    """

    columns: str
    body: TeX

    def __init__(self, columns: str, *body: TeX | str) -> None:
        self.columns = columns
        self.body = _body(body)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.body,)

    @override
    def serialize(self) -> str:
        return (
            f"\\begin{{tabular}}{{{self.columns}}}"
            f"{self.body.serialize()}"
            f"\\end{{tabular}}"
        )


def Flushleft(*body: TeX | str) -> Environment:
    """``\\begin{flushleft} body \\end{flushleft}``."""
    return Environment("flushleft", _body(body))


def Titlepage(*body: TeX | str) -> Environment:
    """``\\begin{titlepage} body \\end{titlepage}``."""
    return Environment("titlepage", _body(body))


__all__ = [
    "Minipage",
    "Put",
    "Picture",
    "MDFramed",
    "LongTable",
    "TabularEnv",
    "Flushleft",
    "Titlepage",
]
