"""Standalone ``\\node`` statement.

Distinguished from the inline ``node`` *path operation* in :mod:`pytex_tikz.path`
because a top-level ``\\node`` always ends in ``;`` and may sit anywhere inside
a ``tikzpicture``, not just on a path.
"""

from dataclasses import dataclass
from typing import override

from pytex import Package, TeX
from pytex.model.raw import coerce_tex

from .coordinate import Coordinate


@dataclass(init=False)
class Node(TeX):
    """``\\node[opts] (name) at (c) {body};`` standalone tikz node."""

    body: TeX
    options: str | None
    name: str | None
    at: Coordinate | None

    def __init__(
        self,
        body: TeX | str,
        *,
        options: str | None = None,
        name: str | None = None,
        at: Coordinate | None = None,
    ) -> None:
        self.body = coerce_tex(body)
        self.options = options
        self.name = name
        self.at = at

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
        nm = f" ({self.name})" if self.name is not None else ""
        pos = f" at {self.at.serialize()}" if self.at is not None else ""
        return f"\\node{opt}{nm}{pos} {{{self.body.serialize()}}};"


@dataclass
class CoordinateNode(TeX):
    """``\\coordinate[opts] (name) at (c);`` — coordinate-only node."""

    name: str
    at: Coordinate | None = None
    options: str | None = None

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
        opt = f"[{self.options}]" if self.options is not None else ""
        pos = f" at {self.at.serialize()}" if self.at is not None else ""
        return f"\\coordinate{opt} ({self.name}){pos};"


__all__ = ["Node", "CoordinateNode"]
