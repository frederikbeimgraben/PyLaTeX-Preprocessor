from ..helpers.with_package import with_package
from ..interface.tex import TeX
from ..model.control_sequence import ControlSequence, Parameter
from ..packages import HYPERREF
from ..registry import Registry

__all__ = [
    "Autoref",
    "Href",
    "Hyperlink",
    "Hypersetup",
    "Hypertarget",
    "Nolinkurl",
    "Url",
]


@Registry.add
@with_package(HYPERREF)
def Hypersetup(options: dict[str, str]) -> TeX:
    return ControlSequence("hypersetup", (Parameter(options),))


@Registry.add
@with_package(HYPERREF)
def Href(url: str, text: TeX | str) -> TeX:
    return ControlSequence("href", (Parameter(url), Parameter(text)))


@Registry.add
@with_package(HYPERREF)
def Url(url: str) -> TeX:
    return ControlSequence("url", (Parameter(url),))


@Registry.add
@with_package(HYPERREF)
def Nolinkurl(url: str) -> TeX:
    return ControlSequence("nolinkurl", (Parameter(url),))


@Registry.add
@with_package(HYPERREF)
def Hyperlink(name: str, text: TeX | str) -> TeX:
    return ControlSequence("hyperlink", (Parameter(name), Parameter(text)))


@Registry.add
@with_package(HYPERREF)
def Hypertarget(name: str, text: TeX | str) -> TeX:
    return ControlSequence("hypertarget", (Parameter(name), Parameter(text)))


@Registry.add
@with_package(HYPERREF)
def Autoref(name: str) -> TeX:
    return ControlSequence("autoref", (Parameter(name),))
