"""TikZ path-operation builder.

TikZ paths are a sequence of *operations* glued together with whitespace and
terminated with ``;``. Every operation is a :class:`PathOp` — a tiny TeX
fragment that does not stand on its own. A :class:`Path` is a :class:`pytex.TeX`
node that emits ``\\<command>[opts] op1 op2 ... ;``.
"""

from dataclasses import dataclass
from typing import override

from pytex import Package, TeX
from pytex.model.raw import coerce_tex

from .coordinate import Coordinate


@dataclass(frozen=True)
class PathOp:
    """A single path operation (e.g. ``-- (3,4)`` or ``node {body}``)."""

    text: str

    def serialize(self) -> str:
        return self.text


def MoveTo(target: Coordinate) -> PathOp:
    """``(x,y)`` — set the current point (used as the first op of a path)."""
    return PathOp(target.serialize())


def LineTo(target: Coordinate) -> PathOp:
    """``-- (x,y)`` — straight line from current point."""
    return PathOp(f"-- {target.serialize()}")


def HorizontalLineTo(target: Coordinate) -> PathOp:
    """``-| (x,y)`` — horizontal then vertical."""
    return PathOp(f"-| {target.serialize()}")


def VerticalLineTo(target: Coordinate) -> PathOp:
    """``|- (x,y)`` — vertical then horizontal."""
    return PathOp(f"|- {target.serialize()}")


def CurveTo(
    target: Coordinate,
    *,
    controls: tuple[Coordinate, Coordinate] | tuple[Coordinate] | None = None,
) -> PathOp:
    """``.. controls <c1> and <c2> .. (x,y)`` Bézier curve."""
    if controls is None:
        return PathOp(f".. {target.serialize()}")
    if len(controls) == 1:
        return PathOp(f".. controls {controls[0].serialize()} .. {target.serialize()}")
    return PathOp(
        f".. controls {controls[0].serialize()} and {controls[1].serialize()}"
        f" .. {target.serialize()}"
    )


def Rectangle(opposite: Coordinate) -> PathOp:
    """``rectangle (x,y)`` — rectangle to the opposite corner."""
    return PathOp(f"rectangle {opposite.serialize()}")


def Circle(radius: float | str) -> PathOp:
    """``circle (radius)`` — circle around the current point."""
    return PathOp(f"circle ({radius})")


def Ellipse(rx: float | str, ry: float | str) -> PathOp:
    """``ellipse (rx and ry)`` — ellipse around the current point."""
    return PathOp(f"ellipse ({rx} and {ry})")


def Arc(start: float, end: float, radius: float | str) -> PathOp:
    """``arc (start:end:radius)`` — circular arc."""
    return PathOp(f"arc ({start}:{end}:{radius})")


def Cycle() -> PathOp:
    """``-- cycle`` — close the path."""
    return PathOp("-- cycle")


def NodeOp(
    body: TeX | str,
    *,
    options: str | None = None,
    name: str | None = None,
    at: Coordinate | None = None,
) -> PathOp:
    """Inline ``node`` operation: ``node[opts] (name) at (c) {body}``."""
    opt = f"[{options}]" if options is not None else ""
    nm = f" ({name})" if name is not None else ""
    pos = f" at {at.serialize()}" if at is not None else ""
    body_str = body.serialize() if isinstance(body, TeX) else body
    return PathOp(f"node{opt}{nm}{pos} {{{body_str}}}")


def EdgeOp(target: Coordinate, *, options: str | None = None) -> PathOp:
    """``edge[opts] (target)`` — to-style edge."""
    opt = f"[{options}]" if options is not None else ""
    return PathOp(f"edge{opt} {target.serialize()}")


def ToOp(target: Coordinate, *, options: str | None = None) -> PathOp:
    """``to[opts] (target)`` — to-style path segment."""
    opt = f"[{options}]" if options is not None else ""
    return PathOp(f"to{opt} {target.serialize()}")


@dataclass(init=False)
class Path(TeX):
    """``\\<command>[opts] op1 op2 ... ;`` — a full tikz path statement.

    Pass either pre-built :class:`PathOp` instances or :class:`Coordinate`
    instances (which are wrapped in a no-op ``MoveTo``) or raw strings (passed
    through verbatim).
    """

    command: str
    options: str | None
    ops: tuple[PathOp, ...]

    def __init__(
        self,
        *ops: PathOp | Coordinate | str,
        command: str = "path",
        options: str | None = None,
    ) -> None:
        self.command = command
        self.options = options
        self.ops = tuple(
            op if isinstance(op, PathOp)
            else PathOp(op.serialize()) if isinstance(op, Coordinate)
            else PathOp(op)
            for op in ops
        )

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
        body = " ".join(op.serialize() for op in self.ops)
        return f"\\{self.command}{opt} {body};"


def Draw(*ops: PathOp | Coordinate | str, options: str | None = None) -> Path:
    """``\\draw[opts] ...;`` — outlined path."""
    return Path(*ops, command="draw", options=options)


def Fill(*ops: PathOp | Coordinate | str, options: str | None = None) -> Path:
    """``\\fill[opts] ...;`` — filled path."""
    return Path(*ops, command="fill", options=options)


def FillDraw(
    *ops: PathOp | Coordinate | str, options: str | None = None
) -> Path:
    """``\\filldraw[opts] ...;`` — filled and outlined path."""
    return Path(*ops, command="filldraw", options=options)


def Shade(*ops: PathOp | Coordinate | str, options: str | None = None) -> Path:
    """``\\shade[opts] ...;`` — shaded path."""
    return Path(*ops, command="shade", options=options)


def Clip(*ops: PathOp | Coordinate | str, options: str | None = None) -> Path:
    """``\\clip[opts] ...;`` — clipping path."""
    return Path(*ops, command="clip", options=options)


# coerce_tex re-export so users can build node bodies without importing pytex.
_ = coerce_tex


__all__ = [
    "PathOp",
    "MoveTo",
    "LineTo",
    "HorizontalLineTo",
    "VerticalLineTo",
    "CurveTo",
    "Rectangle",
    "Circle",
    "Ellipse",
    "Arc",
    "Cycle",
    "NodeOp",
    "EdgeOp",
    "ToOp",
    "Path",
    "Draw",
    "Fill",
    "FillDraw",
    "Shade",
    "Clip",
]
