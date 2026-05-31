from ..interface.tex import TeX
from ..model.control_sequence import ControlSequence, Parameter
from ..model.raw import Raw
from ..registry import Registry


@Registry.add
def Newlength(name: str) -> TeX:
    return ControlSequence("newlength", (Parameter(Raw(name)),))


@Registry.add
def Setlength(name: str, value: str) -> TeX:
    return ControlSequence("setlength", (Parameter(Raw(name)), Parameter(value)))


@Registry.add
def Addtolength(name: str, value: str) -> TeX:
    return ControlSequence(
        "addtolength",
        (Parameter(Raw(name)), Parameter(value)),
    )


@Registry.add
def Settowidth(name: str, body: TeX | str) -> TeX:
    return ControlSequence(
        "settowidth",
        (Parameter(Raw(name)), Parameter(body)),
    )


@Registry.add
def Settoheight(name: str, body: TeX | str) -> TeX:
    return ControlSequence(
        "settoheight",
        (Parameter(Raw(name)), Parameter(body)),
    )


@Registry.add
def Settodepth(name: str, body: TeX | str) -> TeX:
    return ControlSequence(
        "settodepth",
        (Parameter(Raw(name)), Parameter(body)),
    )
