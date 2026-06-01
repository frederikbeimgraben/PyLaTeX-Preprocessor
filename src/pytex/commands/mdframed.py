from ..helpers.with_package import with_package
from ..interface.tex import TeX
from ..model.control_sequence import ControlSequence, Parameter
from ..model.environment import Environment
from ..model.raw import Raw
from ..packages import MDFRAMED
from ..registry import Registry

__all__ = ["Mdfdefinestyle", "Mdframed", "Newmdenv"]


def _opts_to_str(opts: dict[str, str]) -> str:
    return ",".join(k if v == "" else f"{k}={v}" for k, v in opts.items())


@Registry.add
@with_package(MDFRAMED)
def Mdframed(body: TeX | str, options: dict[str, str] | None = None) -> TeX:
    params: tuple[Parameter, ...] = ()
    if options:
        params = (Parameter(Raw(_opts_to_str(options)), optional=True),)
    return Environment("mdframed", body, params)


@Registry.add
@with_package(MDFRAMED)
def Mdfdefinestyle(name: str, options: dict[str, str]) -> TeX:
    return ControlSequence(
        "mdfdefinestyle",
        (Parameter(name), Parameter(Raw(_opts_to_str(options)))),
    )


@Registry.add
@with_package(MDFRAMED)
def Newmdenv(name: str, options: dict[str, str]) -> TeX:
    return ControlSequence(
        "newmdenv",
        (
            Parameter(Raw(_opts_to_str(options)), optional=True),
            Parameter(name),
        ),
    )
