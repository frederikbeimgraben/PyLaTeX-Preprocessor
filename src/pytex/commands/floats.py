"""Factories for float environments, multi-column text and the title page."""

from ..helpers.with_package import with_package
from ..interface.tex import TeX
from ..model.control_sequence import ControlSequence, Parameter
from ..model.environment import Environment
from ..packages import FLOAT, FLOATROW
from ..registry import Registry

__all__ = [
    "Columnbreak",
    "Figure",
    "FigureStar",
    "Floatsetup",
    "Minipage",
    "Multicols",
    "Newfloat",
    "Restylefloat",
    "Table",
    "TableStar",
    "Titlepage",
]


def _placed(name: str, body: TeX | str, placement: str | None) -> TeX:
    """Build a float environment with an optional placement specifier.

    If `placement` is None, the environment gets no optional argument.
    """
    if placement is None:
        return Environment(name, body)
    return Environment(name, body, (Parameter(placement, optional=True),))


@Registry.add
def Figure(body: TeX | str, placement: str | None = None) -> TeX:
    """Render a `figure` environment.

    Args:
        placement: The LaTeX placement specifier, for example `htbp`. If
            `placement` is None, the environment gets no optional argument.
            LaTeX then uses the class default.
    """
    return _placed("figure", body, placement)


@Registry.add
def Table(body: TeX | str, placement: str | None = None) -> TeX:
    """Render a `table` environment.

    Args:
        placement: The LaTeX placement specifier, for example `htbp`. If
            `placement` is None, LaTeX uses the class default.
    """
    return _placed("table", body, placement)


@Registry.add
def FigureStar(body: TeX | str, placement: str | None = None) -> TeX:
    """Render a `figure*` environment, which spans both columns.

    Args:
        placement: The LaTeX placement specifier. A two-column float can only
            go to the top of a page or onto a page of its own.
    """
    return _placed("figure*", body, placement)


@Registry.add
def TableStar(body: TeX | str, placement: str | None = None) -> TeX:
    """Render a `table*` environment, which spans both columns.

    Args:
        placement: The LaTeX placement specifier. A two-column float can only
            go to the top of a page or onto a page of its own.
    """
    return _placed("table*", body, placement)


@Registry.add
def Minipage(width: str, body: TeX | str, align: str | None = None) -> TeX:
    """Render a `minipage` environment.

    Args:
        width: The box width as a LaTeX length, for example `0.5\\textwidth`.
        align: The vertical alignment against the line, one of `t`, `c` or
            `b`. If `align` is None, LaTeX centers the box.
    """
    if align is None:
        return Environment("minipage", body, (Parameter(width),))
    return Environment(
        "minipage",
        body,
        (Parameter(align, optional=True), Parameter(width)),
    )


@Registry.add
@with_package(FLOAT)
def Restylefloat(typ: str) -> TeX:
    """Render `\\restylefloat`, which applies a `float` style to a float type.

    Set the style first with `\\floatstyle`. The `float` package reads the
    current style at this point. PyTeX has no factory for `\\floatstyle`, so
    write that macro with `Raw`.
    """
    return ControlSequence("restylefloat", (Parameter(typ),))


@Registry.add
@with_package(FLOAT)
def Newfloat(typ: str, placement: str, ext: str) -> TeX:
    """Render `\\newfloat`, which defines a float type.

    Args:
        typ: The name of the new float type, for example `program`.
        placement: The default placement specifier, for example `tbp`.
        ext: The extension of the file that holds the list of these floats,
            for example `lop`.
    """
    return ControlSequence(
        "newfloat",
        (Parameter(typ), Parameter(placement), Parameter(ext)),
    )


@Registry.add
@with_package(FLOATROW)
def Floatsetup(options: dict[str, str]) -> TeX:
    """Render `\\floatsetup`, which sets the `floatrow` layout.

    Args:
        options: Float options. The factory renders them as `key=value` pairs
            and joins the pairs with commas.
    """
    return ControlSequence("floatsetup", (Parameter(options),))


@Registry.add
def Multicols(n: int, body: TeX | str) -> TeX:
    """Render a `multicols` environment.

    The environment comes from the `multicol` package, and this factory does
    not name that package requirement. Wrap the node in `WithPackage` to name
    the requirement yourself.

    Args:
        n: The number of columns. The `multicol` package accepts 2 to 10.
    """
    return Environment("multicols", body, (Parameter(str(n)),))


@Registry.add
def Columnbreak() -> TeX:
    """Render `\\columnbreak`, which ends the current column.

    The macro comes from the `multicol` package, and this factory does not
    name that package requirement. Wrap the node in `WithPackage` to name the
    requirement yourself.
    """
    return ControlSequence("columnbreak", ())


@Registry.add
def Titlepage(body: TeX | str) -> TeX:
    """Render a `titlepage` environment, which holds a page of its own."""
    return Environment("titlepage", body)
