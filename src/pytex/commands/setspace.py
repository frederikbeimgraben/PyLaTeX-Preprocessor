from ..helpers.with_package import with_package
from ..interface.tex import TeX
from ..model.control_sequence import ControlSequence, Parameter
from ..model.environment import Environment
from ..packages import SETSPACE
from ..registry import Registry

__all__ = ["Doublespacing", "Onehalfspacing", "Setstretch", "Singlespacing", "Spacing"]


@Registry.add
@with_package(SETSPACE)
def Setstretch(factor: str) -> TeX:
    return ControlSequence("setstretch", (Parameter(factor),))


@Registry.add
@with_package(SETSPACE)
def Singlespacing() -> TeX:
    return ControlSequence("singlespacing", ())


@Registry.add
@with_package(SETSPACE)
def Onehalfspacing() -> TeX:
    return ControlSequence("onehalfspacing", ())


@Registry.add
@with_package(SETSPACE)
def Doublespacing() -> TeX:
    return ControlSequence("doublespacing", ())


@Registry.add
@with_package(SETSPACE)
def Spacing(factor: str, body: TeX | str) -> TeX:
    return Environment("spacing", body, (Parameter(factor),))
