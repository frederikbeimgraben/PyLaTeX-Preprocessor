from ..helpers.with_package import with_package
from ..interface.tex import TeX
from ..model.control_sequence import ControlSequence, Parameter
from ..model.environment import Environment
from ..packages import FLOAT, FLOATROW
from ..registry import Registry


def _placed(name: str, body: TeX | str, placement: str | None) -> TeX:
    if placement is None:
        return Environment(name, body)
    return Environment(name, body, (Parameter(placement, optional=True),))


@Registry.add
def Figure(body: TeX | str, placement: str | None = None) -> TeX:
    return _placed("figure", body, placement)


@Registry.add
def Table(body: TeX | str, placement: str | None = None) -> TeX:
    return _placed("table", body, placement)


@Registry.add
def FigureStar(body: TeX | str, placement: str | None = None) -> TeX:
    return _placed("figure*", body, placement)


@Registry.add
def TableStar(body: TeX | str, placement: str | None = None) -> TeX:
    return _placed("table*", body, placement)


@Registry.add
def Minipage(width: str, body: TeX | str, align: str | None = None) -> TeX:
    if align is None:
        return Environment("minipage", body, (Parameter(width),))
    return Environment(
        "minipage",
        body,
        (Parameter(align, optional=True), Parameter(width)),
    )


@Registry.add
@with_package(FLOAT)
def Restylefloat(typ: str) -> TeX:
    return ControlSequence("restylefloat", (Parameter(typ),))


@Registry.add
@with_package(FLOAT)
def Newfloat(typ: str, placement: str, ext: str) -> TeX:
    return ControlSequence(
        "newfloat",
        (Parameter(typ), Parameter(placement), Parameter(ext)),
    )


@Registry.add
@with_package(FLOATROW)
def Floatsetup(options: dict[str, str]) -> TeX:
    return ControlSequence("floatsetup", (Parameter(options),))
