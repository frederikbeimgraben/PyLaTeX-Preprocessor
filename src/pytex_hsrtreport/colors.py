"""Custom colour definitions used by the HSRT report layout."""

from dataclasses import dataclass
from typing import override

from pytex import Package, TeX

#: name -> rgb triple, copied from the original ``InfoBlocks.tex``.
COLOR_DEFS: dict[str, tuple[float, float, float]] = {
    "britishracinggreen": (0.0, 0.26, 0.15),
    "eggplant": (0.38, 0.25, 0.32),
    "hanblue": (0.27, 0.42, 0.81),
    "navyblue": (0.0, 0.0, 0.5),
    "pansypurple": (0.47, 0.09, 0.29),
    "shockingpink": (0.99, 0.06, 0.75),
}


@dataclass
class DefineColor(TeX):
    """``\\definecolor{name}{model}{spec}`` — requires xcolor."""

    name: str
    spec: str
    model: str = "rgb"

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return {"xcolor"}

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return f"\\definecolor{{{self.name}}}{{{self.model}}}{{{self.spec}}}"


def colors_block() -> str:
    """Serialized ``\\definecolor`` list for all HSRT custom colours."""
    return "\n".join(
        DefineColor(name, ", ".join(str(c) for c in rgb)).serialize()
        for name, rgb in COLOR_DEFS.items()
    )
