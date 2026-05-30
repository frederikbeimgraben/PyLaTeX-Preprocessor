"""Native TikZ support for PyTeX.

Strongly-typed Python wrappers for every piece a tikz figure usually needs:

* :class:`Coordinate` — cartesian / polar / named / relative / page coords.
* :class:`TikzPicture`, :class:`Scope` — environments.
* :class:`Node`, :class:`CoordinateNode` — standalone ``\\node`` / ``\\coordinate``.
* :class:`Path`, :func:`Draw`, :func:`Fill`, :func:`FillDraw`, :func:`Shade`,
  :func:`Clip` — full path statements built from :class:`PathOp` ops
  (:func:`MoveTo`, :func:`LineTo`, :func:`CurveTo`, :func:`Rectangle`,
  :func:`Circle`, :func:`Ellipse`, :func:`Arc`, :func:`Cycle`, :func:`NodeOp`,
  :func:`EdgeOp`, :func:`ToOp`).
* :class:`TikzSet`, :class:`UseTikzLibrary`, :class:`PgfMathSetMacro` —
  preamble / configuration commands.
* :class:`ForEach`, :func:`unroll` — Python-side replacement for tikz's
  ``\\foreach`` (the loop runs at build time, the result is a flat Block of
  TeX nodes).

Example::

    from pytex import Group
    from pytex_tikz import (
        Coordinate, TikzPicture, Draw, MoveTo, LineTo, Rectangle, Node,
    )

    pic = TikzPicture(
        Draw(
            MoveTo(Coordinate.cartesian(0, 0)),
            LineTo(Coordinate.cartesian(2, 1)),
            options="thick, blue",
        ),
        Draw(
            Coordinate.cartesian(0, 0),
            Rectangle(Coordinate.cartesian(1, 1)),
            options="fill=red!20",
        ),
        Node("hello", at=Coordinate.cartesian(1, 0.5), name="lbl"),
        options="scale=1",
    )
    print(pic.serialize())
"""

from .coordinate import Coordinate
from .foreach import ForEach, unroll
from .node import CoordinateNode, Node
from .path import (
    Arc,
    Circle,
    Clip,
    CurveTo,
    Cycle,
    Draw,
    EdgeOp,
    Ellipse,
    Fill,
    FillDraw,
    HorizontalLineTo,
    LineTo,
    MoveTo,
    NodeOp,
    Path,
    PathOp,
    Rectangle,
    Shade,
    ToOp,
    VerticalLineTo,
)
from .picture import (
    PgfMathSetMacro,
    Scope,
    TikzContent,
    TikzPicture,
    TikzSet,
    UseTikzLibrary,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    # Coordinate
    "Coordinate",
    # Environments
    "TikzPicture",
    "Scope",
    # Standalone nodes
    "Node",
    "CoordinateNode",
    # Path commands
    "Path",
    "Draw",
    "Fill",
    "FillDraw",
    "Shade",
    "Clip",
    # Path operations
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
    # Preamble helpers
    "TikzSet",
    "UseTikzLibrary",
    "PgfMathSetMacro",
    # Content type alias
    "TikzContent",
    # Foreach unroll
    "ForEach",
    "unroll",
]
