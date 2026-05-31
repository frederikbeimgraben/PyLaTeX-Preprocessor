from ..helpers.with_package import with_package
from ..interface.tex import TeX
from ..model.control_sequence import ControlSequence, Parameter
from ..packages import ETOOLBOX, IFTHEN
from ..registry import Registry


@Registry.add
@with_package(IFTHEN)
def Ifthenelse(condition: TeX | str, then: TeX | str, otherwise: TeX | str) -> TeX:
    return ControlSequence(
        "ifthenelse",
        (Parameter(condition), Parameter(then), Parameter(otherwise)),
    )


@Registry.add
@with_package(IFTHEN)
def Equal(a: TeX | str, b: TeX | str) -> TeX:
    return ControlSequence("equal", (Parameter(a), Parameter(b)))


@Registry.add
@with_package(ETOOLBOX)
def Ifstrequal(a: TeX | str, b: TeX | str, then: TeX | str, otherwise: TeX | str) -> TeX:
    return ControlSequence(
        "ifstrequal",
        (Parameter(a), Parameter(b), Parameter(then), Parameter(otherwise)),
    )


@Registry.add
@with_package(ETOOLBOX)
def Ifdefstring(cmd: str, target: TeX | str, then: TeX | str, otherwise: TeX | str) -> TeX:
    return ControlSequence(
        "ifdefstring",
        (Parameter(cmd), Parameter(target), Parameter(then), Parameter(otherwise)),
    )


@Registry.add
@with_package(ETOOLBOX)
def Pretocmd(cmd: str, prepend: TeX | str) -> TeX:
    return ControlSequence(
        "pretocmd",
        (Parameter(cmd), Parameter(prepend), Parameter(""), Parameter("")),
    )


@Registry.add
@with_package(ETOOLBOX)
def Apptocmd(cmd: str, append: TeX | str) -> TeX:
    return ControlSequence(
        "apptocmd",
        (Parameter(cmd), Parameter(append), Parameter(""), Parameter("")),
    )
