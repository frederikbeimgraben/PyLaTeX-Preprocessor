"""Factories for LaTeX hooks that run code at a given point."""

from ..helpers.with_package import with_package
from ..interface.tex import TeX
from ..model.control_sequence import ControlSequence, Parameter
from ..packages import ETOOLBOX
from ..registry import Registry

__all__ = [
    "AtBeginDocument",
    "AtBeginEnvironment",
    "AtBeginPage",
    "AtEndDocument",
    "AtEndEnvironment",
    "AtEndOfClass",
    "AtEndOfPackage",
]


@Registry.add
def AtBeginDocument(body: TeX | str) -> TeX:
    """Render `\\AtBeginDocument`, which runs the body at `\\begin{document}`.

    Put this node in the preamble. LaTeX allows `\\AtBeginDocument` in the
    preamble only, and it stops the compile pass with an error anywhere else.
    """
    return ControlSequence("AtBeginDocument", (Parameter(body),))


@Registry.add
def AtEndDocument(body: TeX | str) -> TeX:
    """Render `\\AtEndDocument`, which runs the body at `\\end{document}`."""
    return ControlSequence("AtEndDocument", (Parameter(body),))


@Registry.add
@with_package(ETOOLBOX)
def AtBeginEnvironment(env: str, body: TeX | str) -> TeX:
    """Render `\\AtBeginEnvironment`, which runs the body at each environment start.

    Args:
        env: The environment name, without a backslash, for example `figure`.
    """
    return ControlSequence(
        "AtBeginEnvironment",
        (Parameter(env), Parameter(body)),
    )


@Registry.add
@with_package(ETOOLBOX)
def AtEndEnvironment(env: str, body: TeX | str) -> TeX:
    """Render `\\AtEndEnvironment`, which runs the body at each environment end.

    Args:
        env: The environment name, without a backslash, for example `figure`.
    """
    return ControlSequence(
        "AtEndEnvironment",
        (Parameter(env), Parameter(body)),
    )


@Registry.add
def AtBeginPage(body: TeX | str) -> TeX:
    """Render `\\AtBeginPage` with the body.

    The LaTeX kernel does not define `\\AtBeginPage`, and this factory names
    no package requirement. Define the macro yourself before you use this
    factory.
    """
    return ControlSequence("AtBeginPage", (Parameter(body),))


@Registry.add
def AtEndOfPackage(body: TeX | str) -> TeX:
    """Render `\\AtEndOfPackage`, which runs the body at the end of a package.

    Use it inside a `.sty` file only.
    """
    return ControlSequence("AtEndOfPackage", (Parameter(body),))


@Registry.add
def AtEndOfClass(body: TeX | str) -> TeX:
    """Render `\\AtEndOfClass`, which runs the body at the end of a class.

    Use it inside a `.cls` file only.
    """
    return ControlSequence("AtEndOfClass", (Parameter(body),))
