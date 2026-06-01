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
    return ControlSequence(
        "definecolor",
        (Parameter(name), Parameter(model), Parameter(spec)),
    )


@Registry.add
@with_package(XCOLOR)
def Textcolor(color: str, body: TeX | str) -> TeX:
    return ControlSequence("textcolor", (Parameter(color), Parameter(body)))


@Registry.add
@with_package(XCOLOR)
def SelectColor(color: str) -> TeX:
    """`\\color{name}` — switch current colour.

    Use `Color` (model) for typed colour identity.
    """
    return ControlSequence("color", (Parameter(color),))


@Registry.add
@with_package(XCOLOR)
def Colorbox(color: str, body: TeX | str) -> TeX:
    return ControlSequence("colorbox", (Parameter(color), Parameter(body)))


@Registry.add
@with_package(XCOLOR)
def Fcolorbox(border: str, fill: str, body: TeX | str) -> TeX:
    return ControlSequence(
        "fcolorbox",
        (Parameter(border), Parameter(fill), Parameter(body)),
    )


@Registry.add
@with_package(XCOLOR)
def Pagecolor(color: str) -> TeX:
    return ControlSequence("pagecolor", (Parameter(color),))
