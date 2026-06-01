from ..helpers.with_package import with_package
from ..interface.tex import TeX
from ..model.control_sequence import ControlSequence, Parameter
from ..packages import CLEVEREF
from ..registry import Registry

__all__ = ["Cref", "CrefUpper", "Crefformat", "Crefname", "CrefnameUpper"]


@Registry.add
@with_package(CLEVEREF)
def Cref(*labels: str) -> TeX:
    return ControlSequence("cref", (Parameter(",".join(labels)),))


@Registry.add
@with_package(CLEVEREF)
def CrefUpper(*labels: str) -> TeX:
    return ControlSequence("Cref", (Parameter(",".join(labels)),))


@Registry.add
@with_package(CLEVEREF)
def Crefname(typ: str, singular: str, plural: str) -> TeX:
    return ControlSequence(
        "crefname",
        (Parameter(typ), Parameter(singular), Parameter(plural)),
    )


@Registry.add
@with_package(CLEVEREF)
def CrefnameUpper(typ: str, singular: str, plural: str) -> TeX:
    return ControlSequence(
        "Crefname",
        (Parameter(typ), Parameter(singular), Parameter(plural)),
    )


@Registry.add
@with_package(CLEVEREF)
def Crefformat(typ: str, fmt: str) -> TeX:
    return ControlSequence("crefformat", (Parameter(typ), Parameter(fmt)))
