from ..interface.tex import TeX
from ..model.control_sequence import ControlSequence, Parameter
from ..registry import Registry


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


@Registry.add
def Tiny() -> TeX:
    return ControlSequence("tiny", ())


@Registry.add
def Scriptsize() -> TeX:
    return ControlSequence("scriptsize", ())


@Registry.add
def Footnotesize() -> TeX:
    return ControlSequence("footnotesize", ())


@Registry.add
def Small() -> TeX:
    return ControlSequence("small", ())


@Registry.add
def Normalsize() -> TeX:
    return ControlSequence("normalsize", ())


@Registry.add
def Large() -> TeX:
    return ControlSequence("large", ())


@Registry.add
def LargeMid() -> TeX:
    return ControlSequence("Large", ())


@Registry.add
def LargeBig() -> TeX:
    return ControlSequence("LARGE", ())


@Registry.add
def Huge() -> TeX:
    return ControlSequence("huge", ())


@Registry.add
def HugeBig() -> TeX:
    return ControlSequence("Huge", ())
