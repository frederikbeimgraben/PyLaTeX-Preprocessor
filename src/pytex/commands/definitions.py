from ..interface.tex import TeX
from ..model.control_sequence import ControlSequence, Parameter
from ..model.raw import Raw
from ..registry import Registry


def _cmd(
    name: str,
    cs: str,
    nargs: int | None,
    default: str | None,
    body: TeX | str,
    star: bool,
) -> TeX:
    full = name + ("*" if star else "")
    params: list[Parameter] = [Parameter(Raw(cs))]
    if nargs is not None:
        params.append(Parameter(str(nargs), optional=True))
        if default is not None:
            params.append(Parameter(default, optional=True))
    params.append(Parameter(body))
    return ControlSequence(full, tuple(params))


@Registry.add
def Newcommand(
    cs: str,
    body: TeX | str,
    nargs: int | None = None,
    default: str | None = None,
    star: bool = False,
) -> TeX:
    return _cmd("newcommand", cs, nargs, default, body, star)


@Registry.add
def Renewcommand(
    cs: str,
    body: TeX | str,
    nargs: int | None = None,
    default: str | None = None,
    star: bool = False,
) -> TeX:
    return _cmd("renewcommand", cs, nargs, default, body, star)


@Registry.add
def Providecommand(
    cs: str,
    body: TeX | str,
    nargs: int | None = None,
    default: str | None = None,
    star: bool = False,
) -> TeX:
    return _cmd("providecommand", cs, nargs, default, body, star)


@Registry.add
def DeclareRobustCommand(
    cs: str,
    body: TeX | str,
    nargs: int | None = None,
    star: bool = False,
) -> TeX:
    return _cmd("DeclareRobustCommand", cs, nargs, None, body, star)


@Registry.add
def Newenvironment(
    name: str,
    begin: TeX | str,
    end: TeX | str,
    nargs: int | None = None,
) -> TeX:
    params: list[Parameter] = [Parameter(name)]
    if nargs is not None:
        params.append(Parameter(str(nargs), optional=True))
    params.extend([Parameter(begin), Parameter(end)])
    return ControlSequence("newenvironment", tuple(params))


@Registry.add
def Renewenvironment(
    name: str,
    begin: TeX | str,
    end: TeX | str,
    nargs: int | None = None,
) -> TeX:
    params: list[Parameter] = [Parameter(name)]
    if nargs is not None:
        params.append(Parameter(str(nargs), optional=True))
    params.extend([Parameter(begin), Parameter(end)])
    return ControlSequence("renewenvironment", tuple(params))


@Registry.add
def Def(cs: str, body: TeX | str) -> TeX:
    """Low-level TeX \\def — use sparingly."""
    return Raw(f"\\def\\{cs}{{{body}}}")
