from ..interface.tex import TeX
from ..model.control_sequence import ControlSequence, Parameter
from ..registry import Registry

__all__ = [
    "LARGE",
    "Bfseries",
    "Fontsize",
    "Huge",
    "Itshape",
    "Large",
    "Mdseries",
    "Normalfont",
    "Rmfamily",
    "Scshape",
    "Selectfont",
    "Sffamily",
    "Slshape",
    "Ttfamily",
    "Upshape",
    "footnotesize",
    "huge",
    "large",
    "normalsize",
    "scriptsize",
    "small",
    "tiny",
]


@Registry.add
def Fontsize(size: str, baseline: str) -> TeX:
    return ControlSequence("fontsize", (Parameter(size), Parameter(baseline)))


@Registry.add
def Selectfont() -> TeX:
    return ControlSequence("selectfont", ())


@Registry.add
def Rmfamily() -> TeX:
    return ControlSequence("rmfamily", ())


@Registry.add
def Sffamily() -> TeX:
    return ControlSequence("sffamily", ())


@Registry.add
def Ttfamily() -> TeX:
    return ControlSequence("ttfamily", ())


@Registry.add
def Bfseries() -> TeX:
    return ControlSequence("bfseries", ())


@Registry.add
def Mdseries() -> TeX:
    return ControlSequence("mdseries", ())


@Registry.add
def Itshape() -> TeX:
    return ControlSequence("itshape", ())


@Registry.add
def Slshape() -> TeX:
    return ControlSequence("slshape", ())


@Registry.add
def Scshape() -> TeX:
    return ControlSequence("scshape", ())


@Registry.add
def Upshape() -> TeX:
    return ControlSequence("upshape", ())


@Registry.add
def Normalfont() -> TeX:
    return ControlSequence("normalfont", ())


# Size switches use the LaTeX command spelling verbatim as the factory name:
# `\large`/`\Large`/`\LARGE` and `\huge`/`\Huge` differ only by case, which
# PascalCase cannot encode without a collision. Python identifiers are
# case-sensitive, so `large`/`Large`/`LARGE` map one-to-one and predictably.
@Registry.add
def tiny() -> TeX:
    return ControlSequence("tiny", ())


@Registry.add
def scriptsize() -> TeX:
    return ControlSequence("scriptsize", ())


@Registry.add
def footnotesize() -> TeX:
    return ControlSequence("footnotesize", ())


@Registry.add
def small() -> TeX:
    return ControlSequence("small", ())


@Registry.add
def normalsize() -> TeX:
    return ControlSequence("normalsize", ())


@Registry.add
def large() -> TeX:
    return ControlSequence("large", ())


@Registry.add
def Large() -> TeX:
    return ControlSequence("Large", ())


@Registry.add
def LARGE() -> TeX:
    return ControlSequence("LARGE", ())


@Registry.add
def huge() -> TeX:
    return ControlSequence("huge", ())


@Registry.add
def Huge() -> TeX:
    return ControlSequence("Huge", ())
