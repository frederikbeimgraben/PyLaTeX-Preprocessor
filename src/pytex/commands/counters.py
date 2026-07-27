"""Factories for LaTeX counters."""

from ..interface.tex import TeX
from ..model.control_sequence import ControlSequence, Parameter
from ..model.raw import Raw
from ..registry import Registry

__all__ = [
    "Addtocounter",
    "Alph",
    "AlphUpper",
    "Arabic",
    "Newcounter",
    "Refstepcounter",
    "RomanCounter",
    "RomanCounterUpper",
    "Setcounter",
    "Stepcounter",
    "UseCounter",
    "Value",
]


@Registry.add
def Newcounter(name: str, within: str | None = None) -> TeX:
    """Render `\\newcounter`, which defines a counter.

    Args:
        within: The parent counter. LaTeX resets the new counter each time the
            parent counter steps. If `within` is None, nothing resets it.
    """
    if within is None:
        return ControlSequence("newcounter", (Parameter(name),))
    return ControlSequence(
        "newcounter",
        (Parameter(name), Parameter(within, optional=True)),
    )


@Registry.add
def Setcounter(name: str, value: int | str) -> TeX:
    """Render `\\setcounter`, which sets a counter to a value."""
    return ControlSequence("setcounter", (Parameter(name), Parameter(str(value))))


@Registry.add
def Addtocounter(name: str, value: int | str) -> TeX:
    """Render `\\addtocounter`, which adds a value to a counter."""
    return ControlSequence("addtocounter", (Parameter(name), Parameter(str(value))))


@Registry.add
def Stepcounter(name: str) -> TeX:
    """Render `\\stepcounter`, which adds one to a counter.

    LaTeX also resets every counter that this counter controls.
    """
    return ControlSequence("stepcounter", (Parameter(name),))


@Registry.add
def Refstepcounter(name: str) -> TeX:
    """Render `\\refstepcounter`, which adds one to a counter.

    The new value also becomes the target of the next `\\label`.
    """
    return ControlSequence("refstepcounter", (Parameter(name),))


@Registry.add
def Value(name: str) -> TeX:
    """Render `\\value`, which reads a counter as a number.

    Use it where LaTeX expects a number, for example inside `\\setcounter`.
    """
    return ControlSequence("value", (Parameter(name),))


@Registry.add
def Arabic(name: str) -> TeX:
    """Render `\\arabic`, which prints a counter as Arabic numerals."""
    return ControlSequence("arabic", (Parameter(name),))


@Registry.add
def RomanCounter(name: str) -> TeX:
    """Render `\\roman`, which prints a counter as lowercase Roman numerals."""
    return ControlSequence("roman", (Parameter(name),))


@Registry.add
def RomanCounterUpper(name: str) -> TeX:
    """Render `\\Roman`, which prints a counter as uppercase Roman numerals."""
    return ControlSequence("Roman", (Parameter(name),))


@Registry.add
def Alph(name: str) -> TeX:
    """Render `\\alph`, which prints a counter as a lowercase letter."""
    return ControlSequence("alph", (Parameter(name),))


@Registry.add
def AlphUpper(name: str) -> TeX:
    """Render `\\Alph`, which prints a counter as an uppercase letter."""
    return ControlSequence("Alph", (Parameter(name),))


@Registry.add
def UseCounter(name: str) -> TeX:
    """Render the print form of a counter, for example `\\thepage`.

    Args:
        name: The counter name. The factory writes it into the macro name, so
            `page` gives `\\thepage`.
    """
    return Raw(f"\\the{name}")
