from ..helpers.with_package import with_package
from ..interface.tex import TeX
from ..model.control_sequence import ControlSequence, Parameter
from ..packages import ETOOLBOX
from ..registry import Registry


@Registry.add
def AtBeginDocument(body: TeX | str) -> TeX:
    return ControlSequence("AtBeginDocument", (Parameter(body),))


@Registry.add
def AtEndDocument(body: TeX | str) -> TeX:
    return ControlSequence("AtEndDocument", (Parameter(body),))


@Registry.add
@with_package(ETOOLBOX)
def AtBeginEnvironment(env: str, body: TeX | str) -> TeX:
    return ControlSequence(
        "AtBeginEnvironment",
        (Parameter(env), Parameter(body)),
    )


@Registry.add
@with_package(ETOOLBOX)
def AtEndEnvironment(env: str, body: TeX | str) -> TeX:
    return ControlSequence(
        "AtEndEnvironment",
        (Parameter(env), Parameter(body)),
    )


@Registry.add
def AtBeginPage(body: TeX | str) -> TeX:
    return ControlSequence("AtBeginPage", (Parameter(body),))


@Registry.add
def AtEndOfPackage(body: TeX | str) -> TeX:
    return ControlSequence("AtEndOfPackage", (Parameter(body),))


@Registry.add
def AtEndOfClass(body: TeX | str) -> TeX:
    return ControlSequence("AtEndOfClass", (Parameter(body),))
