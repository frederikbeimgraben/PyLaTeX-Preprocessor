"""Factories for the `mdframed` package."""

from ..helpers.with_package import with_package
from ..interface.tex import TeX
from ..model.control_sequence import ControlSequence, Parameter
from ..model.environment import Environment
from ..model.raw import Raw
from ..packages import MDFRAMED
from ..registry import Registry

__all__ = ["Mdfdefinestyle", "Mdframed", "Newmdenv"]


def _opts_to_str(opts: dict[str, str]) -> str:
    """Join frame options into one comma-separated string.

    A key whose value is an empty string gives a bare option name.
    """
    return ",".join(k if v == "" else f"{k}={v}" for k, v in opts.items())


@Registry.add
@with_package(MDFRAMED)
def Mdframed(body: TeX | str, options: dict[str, str] | None = None) -> TeX:
    """Render an `mdframed` environment, a frame around a block of text.

    Args:
        options: Frame options, for example `{"linecolor": "blue"}`. An empty
            dictionary gives no optional argument.
    """
    params: tuple[Parameter, ...] = ()
    if options:
        params = (Parameter(Raw(_opts_to_str(options)), optional=True),)
    return Environment("mdframed", body, params)


@Registry.add
@with_package(MDFRAMED)
def Mdfdefinestyle(name: str, options: dict[str, str]) -> TeX:
    """Render `\\mdfdefinestyle`, which defines a named frame style.

    Pass the name to a later frame as the `style` option.
    """
    return ControlSequence(
        "mdfdefinestyle",
        (Parameter(name), Parameter(Raw(_opts_to_str(options)))),
    )


@Registry.add
@with_package(MDFRAMED)
def Newmdenv(name: str, options: dict[str, str]) -> TeX:
    """Render `\\newmdenv`, which defines a framed environment.

    The factory always renders the optional argument. An empty dictionary
    gives an empty pair of brackets.
    """
    return ControlSequence(
        "newmdenv",
        (
            Parameter(Raw(_opts_to_str(options)), optional=True),
            Parameter(name),
        ),
    )
