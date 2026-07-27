"""Factories for the `geometry` package."""

from ..helpers.with_package import with_package
from ..interface.tex import TeX
from ..model.control_sequence import ControlSequence, Parameter
from ..packages import GEOMETRY
from ..registry import Registry

__all__ = ["Geometry", "Newgeometry", "Restoregeometry"]


@Registry.add
@with_package(GEOMETRY)
def Geometry(options: dict[str, str]) -> TeX:
    """Render `\\geometry`, which sets the page layout.

    Args:
        options: Layout options, for example `{"margin": "2cm"}`. The factory
            renders them as `key=value` pairs and joins the pairs with commas.
    """
    return ControlSequence("geometry", (Parameter(options),))


@Registry.add
@with_package(GEOMETRY)
def Newgeometry(options: dict[str, str]) -> TeX:
    """Render `\\newgeometry`, which changes the layout from this page on.

    Args:
        options: Layout options. `\\newgeometry` accepts margins and sizes
            only. It rejects the paper size and the font size.
    """
    return ControlSequence("newgeometry", (Parameter(options),))


@Registry.add
@with_package(GEOMETRY)
def Restoregeometry() -> TeX:
    """Render `\\restoregeometry`, which returns to the layout of `\\geometry`."""
    return ControlSequence("restoregeometry", ())
