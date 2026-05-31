from ..helpers.with_package import with_package
from ..interface.tex import TeX
from ..model.control_sequence import ControlSequence, Parameter
from ..model.environment import Environment
from ..model.raw import Raw
from ..packages import LISTINGS
from ..registry import Registry


def _render_value(value: object) -> str:
    if isinstance(value, TeX):
        return value.rendered
    return str(value)


def _opts_to_str(opts: dict[str, TeX | str]) -> str:
    return ",".join(f"{k}={_render_value(v)}" for k, v in opts.items())


@Registry.add
@with_package(LISTINGS)
def Lstset(options: dict[str, TeX | str]) -> TeX:
    return ControlSequence("lstset", (Parameter(Raw(_opts_to_str(options))),))


@Registry.add
@with_package(LISTINGS)
def Lstdefinestyle(name: str, options: dict[str, TeX | str]) -> TeX:
    return ControlSequence(
        "lstdefinestyle",
        (Parameter(name), Parameter(Raw(_opts_to_str(options)))),
    )


@Registry.add
@with_package(LISTINGS)
def Lstinputlisting(path: str, options: dict[str, TeX | str] | None = None) -> TeX:
    if options is None:
        return ControlSequence("lstinputlisting", (Parameter(path),))
    return ControlSequence(
        "lstinputlisting",
        (
            Parameter(Raw(_opts_to_str(options)), optional=True),
            Parameter(path),
        ),
    )


@Registry.add
@with_package(LISTINGS)
def Lstinline(body: str, delim: str = "|") -> TeX:
    return Raw(f"\\lstinline{delim}{body}{delim}")


@Registry.add
@with_package(LISTINGS)
def Lstlisting(body: str, options: dict[str, TeX | str] | None = None) -> TeX:
    params: tuple[Parameter, ...] = ()
    if options:
        params = (Parameter(Raw(_opts_to_str(options)), optional=True),)
    return Environment("lstlisting", body, params)
