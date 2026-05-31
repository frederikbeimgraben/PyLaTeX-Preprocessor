from ..helpers.with_package import with_package
from ..interface.tex import TeX
from ..model.control_sequence import ControlSequence, Parameter
from ..packages import GEOMETRY
from ..registry import Registry


@Registry.add
@with_package(GEOMETRY)
def Geometry(options: dict[str, str]) -> TeX:
    return ControlSequence("geometry", (Parameter(options),))


@Registry.add
@with_package(GEOMETRY)
def Newgeometry(options: dict[str, str]) -> TeX:
    return ControlSequence("newgeometry", (Parameter(options),))


@Registry.add
@with_package(GEOMETRY)
def Restoregeometry() -> TeX:
    return ControlSequence("restoregeometry", ())
