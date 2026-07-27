"""Factories for LaTeX tests and macro patching, from `ifthen` and `etoolbox`."""

from ..helpers.with_package import with_package
from ..interface.tex import TeX
from ..model.control_sequence import ControlSequence, Parameter
from ..packages import ETOOLBOX, IFTHEN
from ..registry import Registry

__all__ = ["Apptocmd", "Equal", "Ifdefstring", "Ifstrequal", "Ifthenelse", "Pretocmd"]


@Registry.add
@with_package(IFTHEN)
def Ifthenelse(condition: TeX | str, then: TeX | str, otherwise: TeX | str) -> TeX:
    """Render `\\ifthenelse`, which picks one of two branches.

    Args:
        condition: A test that `ifthen` understands, for example the node that
            `Equal` returns.
    """
    return ControlSequence(
        "ifthenelse",
        (Parameter(condition), Parameter(then), Parameter(otherwise)),
    )


@Registry.add
@with_package(IFTHEN)
def Equal(a: TeX | str, b: TeX | str) -> TeX:
    """Render `\\equal`, the string test that `Ifthenelse` accepts."""
    return ControlSequence("equal", (Parameter(a), Parameter(b)))


@Registry.add
@with_package(ETOOLBOX)
def Ifstrequal(
    a: TeX | str, b: TeX | str, then: TeX | str, otherwise: TeX | str
) -> TeX:
    """Render `\\ifstrequal`, which compares two strings and picks a branch."""
    return ControlSequence(
        "ifstrequal",
        (Parameter(a), Parameter(b), Parameter(then), Parameter(otherwise)),
    )


@Registry.add
@with_package(ETOOLBOX)
def Ifdefstring(
    cmd: str, target: TeX | str, then: TeX | str, otherwise: TeX | str
) -> TeX:
    """Render `\\ifdefstring`, which compares a macro body to a string.

    Args:
        cmd: The macro, with the backslash, for example `\\foo`.
    """
    return ControlSequence(
        "ifdefstring",
        (Parameter(cmd), Parameter(target), Parameter(then), Parameter(otherwise)),
    )


@Registry.add
@with_package(ETOOLBOX)
def Pretocmd(cmd: str, prepend: TeX | str) -> TeX:
    """Render `\\pretocmd`, which adds text to the start of a macro.

    The factory passes an empty success branch and an empty failure branch.
    etoolbox needs both arguments. A patch that fails gives no message.

    Args:
        cmd: The macro to patch, with the backslash, for example `\\section`.
    """
    return ControlSequence(
        "pretocmd",
        (Parameter(cmd), Parameter(prepend), Parameter(""), Parameter("")),
    )


@Registry.add
@with_package(ETOOLBOX)
def Apptocmd(cmd: str, append: TeX | str) -> TeX:
    """Render `\\apptocmd`, which adds text to the end of a macro.

    The factory passes an empty success branch and an empty failure branch.
    etoolbox needs both arguments. A patch that fails gives no message.

    Args:
        cmd: The macro to patch, with the backslash, for example `\\section`.
    """
    return ControlSequence(
        "apptocmd",
        (Parameter(cmd), Parameter(append), Parameter(""), Parameter("")),
    )
