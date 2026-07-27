"""Factories for the `xcolor` package."""

from ..helpers.with_package import with_package
from ..interface.tex import TeX
from ..model.control_sequence import ControlSequence, Parameter
from ..packages import XCOLOR
from ..registry import Registry

__all__ = [
    "Colorbox",
    "Definecolor",
    "Fcolorbox",
    "Pagecolor",
    "SelectColor",
    "Textcolor",
]


@Registry.add
@with_package(XCOLOR)
def Definecolor(name: str, model: str, spec: str) -> TeX:
    """Render `\\definecolor`, which defines a named color.

    Args:
        model: The color model, for example `rgb`, `HTML` or `gray`.
        spec: The values for that model, for example `1,0,0` or `FF0000`.
    """
    return ControlSequence(
        "definecolor",
        (Parameter(name), Parameter(model), Parameter(spec)),
    )


@Registry.add
@with_package(XCOLOR)
def Textcolor(color: str, body: TeX | str) -> TeX:
    """Render `\\textcolor`, which prints the body in the named color."""
    return ControlSequence("textcolor", (Parameter(color), Parameter(body)))


@Registry.add
@with_package(XCOLOR)
def SelectColor(color: str) -> TeX:
    """Render `\\color`, which switches the current color.

    The switch holds to the end of the current TeX group. Use the `Color`
    model class when you need a typed color value.
    """
    return ControlSequence("color", (Parameter(color),))


@Registry.add
@with_package(XCOLOR)
def Colorbox(color: str, body: TeX | str) -> TeX:
    """Render `\\colorbox`, which puts the body on a colored background."""
    return ControlSequence("colorbox", (Parameter(color), Parameter(body)))


@Registry.add
@with_package(XCOLOR)
def Fcolorbox(border: str, fill: str, body: TeX | str) -> TeX:
    """Render `\\fcolorbox`, a colored box with a colored frame."""
    return ControlSequence(
        "fcolorbox",
        (Parameter(border), Parameter(fill), Parameter(body)),
    )


@Registry.add
@with_package(XCOLOR)
def Pagecolor(color: str) -> TeX:
    """Render `\\pagecolor`, which sets the page background color."""
    return ControlSequence("pagecolor", (Parameter(color),))
