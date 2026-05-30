"""Custom colours used by the HSRT report layout.

* :data:`COLOR_DEFS` — rgb spec for every custom colour.
* :class:`DefineColor` — emits ``\\definecolor{name}{model}{spec}``.
* :func:`colors_block` — Block of all DefineColors (preamble registration).
* :class:`HSRTColor` — string enum of all known colour names. Used as the
  identifier in TeX-side ``\\color``/``\\textcolor`` calls.
* ``ColorBritishRacingGreen(child)``, ``ColorEggplant(child)``, ... — one
  helper per custom colour, returning ``\\textcolor{name}{child}``.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import override

from pytex import BuiltinPackages, Package, TeX
from pytex.library import TextColor
from pytex_komascript.model import Block

#: name -> rgb triple, copied from the original ``InfoBlocks.tex``.
COLOR_DEFS: dict[str, tuple[float, float, float]] = {
    "britishracinggreen": (0.0, 0.26, 0.15),
    "eggplant": (0.38, 0.25, 0.32),
    "hanblue": (0.27, 0.42, 0.81),
    "navyblue": (0.0, 0.0, 0.5),
    "pansypurple": (0.47, 0.09, 0.29),
    "shockingpink": (0.99, 0.06, 0.75),
}


class HSRTColor(StrEnum):
    """Enum of HSRT custom colour names — string-valued so they can be used
    directly as the colour identifier in ``\\textcolor{...}{...}``.
    """

    BRITISH_RACING_GREEN = "britishracinggreen"
    EGGPLANT = "eggplant"
    HANBLUE = "hanblue"
    NAVYBLUE = "navyblue"
    PANSYPURPLE = "pansypurple"
    SHOCKINGPINK = "shockingpink"


@dataclass
class DefineColor(TeX):
    """``\\definecolor{name}{model}{spec}`` — requires xcolor."""

    name: str
    spec: str
    model: str = "rgb"

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return {BuiltinPackages.XCOLOR.value}

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return f"\\definecolor{{{self.name}}}{{{self.model}}}{{{self.spec}}}"


def colors_block() -> TeX:
    """:class:`Block` of ``\\definecolor`` calls for all custom colours."""
    return Block(
        *(
            DefineColor(name, ", ".join(str(c) for c in rgb))
            for name, rgb in COLOR_DEFS.items()
        )
    )


def Color(color: HSRTColor | str, child: TeX | str) -> TeX:
    """Generic ``\\textcolor{name}{child}`` — accepts any registered colour."""
    return TextColor(str(color), child)


def ColorBritishRacingGreen(child: TeX | str) -> TeX:
    return TextColor(HSRTColor.BRITISH_RACING_GREEN, child)


def ColorEggplant(child: TeX | str) -> TeX:
    return TextColor(HSRTColor.EGGPLANT, child)


def ColorHanblue(child: TeX | str) -> TeX:
    return TextColor(HSRTColor.HANBLUE, child)


def ColorNavyblue(child: TeX | str) -> TeX:
    return TextColor(HSRTColor.NAVYBLUE, child)


def ColorPansypurple(child: TeX | str) -> TeX:
    return TextColor(HSRTColor.PANSYPURPLE, child)


def ColorShockingpink(child: TeX | str) -> TeX:
    return TextColor(HSRTColor.SHOCKINGPINK, child)


__all__ = [
    "COLOR_DEFS",
    "HSRTColor",
    "DefineColor",
    "colors_block",
    "Color",
    "ColorBritishRacingGreen",
    "ColorEggplant",
    "ColorHanblue",
    "ColorNavyblue",
    "ColorPansypurple",
    "ColorShockingpink",
]
