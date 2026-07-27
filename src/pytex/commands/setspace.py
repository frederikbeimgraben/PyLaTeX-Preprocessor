"""Factories for the `setspace` package."""

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
    """Render `\\setstretch`, which sets the line spacing factor.

    Args:
        factor: The spacing factor as a decimal number, for example `1.5`.
    """
    return ControlSequence("setstretch", (Parameter(factor),))


@Registry.add
@with_package(SETSPACE)
def Singlespacing() -> TeX:
    """Render `\\singlespacing`, which sets single line spacing."""
    return ControlSequence("singlespacing", ())


@Registry.add
@with_package(SETSPACE)
def Onehalfspacing() -> TeX:
    """Render `\\onehalfspacing`, which sets one-and-a-half line spacing."""
    return ControlSequence("onehalfspacing", ())


@Registry.add
@with_package(SETSPACE)
def Doublespacing() -> TeX:
    """Render `\\doublespacing`, which sets double line spacing."""
    return ControlSequence("doublespacing", ())


@Registry.add
@with_package(SETSPACE)
def Spacing(factor: str, body: TeX | str) -> TeX:
    """Render a `spacing` environment, which sets the spacing for one block.

    Args:
        factor: The spacing factor as a decimal number, for example `1.5`.
    """
    return Environment("spacing", body, (Parameter(factor),))
