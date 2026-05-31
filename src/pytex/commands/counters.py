from ..interface.tex import TeX
from ..model.control_sequence import ControlSequence, Parameter
from ..model.raw import Raw
from ..registry import Registry


@Registry.add
def Newcounter(name: str, within: str | None = None) -> TeX:
    if within is None:
        return ControlSequence("newcounter", (Parameter(name),))
    return ControlSequence(
        "newcounter",
        (Parameter(name), Parameter(within, optional=True)),
    )


@Registry.add
def Setcounter(name: str, value: int | str) -> TeX:
    return ControlSequence("setcounter", (Parameter(name), Parameter(str(value))))


@Registry.add
def Addtocounter(name: str, value: int | str) -> TeX:
    return ControlSequence(
        "addtocounter", (Parameter(name), Parameter(str(value)))
    )


@Registry.add
def Stepcounter(name: str) -> TeX:
    return ControlSequence("stepcounter", (Parameter(name),))


@Registry.add
def Refstepcounter(name: str) -> TeX:
    return ControlSequence("refstepcounter", (Parameter(name),))


@Registry.add
def Value(name: str) -> TeX:
    return ControlSequence("value", (Parameter(name),))


@Registry.add
def Arabic(name: str) -> TeX:
    return ControlSequence("arabic", (Parameter(name),))


@Registry.add
def RomanCounter(name: str) -> TeX:
    return ControlSequence("roman", (Parameter(name),))


@Registry.add
def RomanCounterUpper(name: str) -> TeX:
    return ControlSequence("Roman", (Parameter(name),))


@Registry.add
def Alph(name: str) -> TeX:
    return ControlSequence("alph", (Parameter(name),))


@Registry.add
def AlphUpper(name: str) -> TeX:
    return ControlSequence("Alph", (Parameter(name),))


@Registry.add
def UseCounter(name: str) -> TeX:
    """Render `\\thecounter` for given counter name."""
    return Raw(f"\\the{name}")
