from ..helpers.with_package import with_package
from ..interface.tex import TeX
from ..model.control_sequence import ControlSequence, Parameter
from ..model.raw import Raw
from ..packages import FONTSPEC
from ..registry import Registry

__all__ = [
    "Newfontfamily",
    "Setfontfamilies",
    "Setmainfont",
    "Setmonofont",
    "Setsansfont",
]


def _opts_to_str(opts: dict[str, str]) -> str:
    return ",".join(k if v == "" else f"{k}={v}" for k, v in opts.items())


@Registry.add
@with_package(FONTSPEC)
def Setmainfont(font: str, options: dict[str, str] | None = None) -> TeX:
    if options is None:
        return ControlSequence("setmainfont", (Parameter(font),))
    return ControlSequence(
        "setmainfont",
        (Parameter(font), Parameter(Raw(_opts_to_str(options)), optional=True)),
    )


@Registry.add
@with_package(FONTSPEC)
def Setsansfont(font: str, options: dict[str, str] | None = None) -> TeX:
    if options is None:
        return ControlSequence("setsansfont", (Parameter(font),))
    return ControlSequence(
        "setsansfont",
        (Parameter(font), Parameter(Raw(_opts_to_str(options)), optional=True)),
    )


@Registry.add
@with_package(FONTSPEC)
def Setmonofont(font: str, options: dict[str, str] | None = None) -> TeX:
    if options is None:
        return ControlSequence("setmonofont", (Parameter(font),))
    return ControlSequence(
        "setmonofont",
        (Parameter(font), Parameter(Raw(_opts_to_str(options)), optional=True)),
    )


@Registry.add
@with_package(FONTSPEC)
def Newfontfamily(cmd: str, font: str, options: dict[str, str] | None = None) -> TeX:
    if options is None:
        return ControlSequence(
            "newfontfamily",
            (Parameter(Raw(cmd)), Parameter(font)),
        )
    return ControlSequence(
        "newfontfamily",
        (
            Parameter(Raw(cmd)),
            Parameter(font),
            Parameter(Raw(_opts_to_str(options)), optional=True),
        ),
    )


@Registry.add
@with_package(FONTSPEC)
def Setfontfamilies(font: str) -> TeX:
    return ControlSequence("setfontfamilies", (Parameter(font),))
