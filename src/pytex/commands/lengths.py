import warnings

from ..interface.tex import TeX
from ..model.control_sequence import ControlSequence, Parameter
from ..model.length import Length
from ..model.raw import Raw
from ..registry import Registry

__all__ = [
    "Addtolength",
    "Arraystretch_len",
    "Baselineskip",
    "Baselinestretch",
    "Columnsep",
    "Columnwidth",
    "Fill_len",
    "Footskip",
    "Headheight",
    "Headsep",
    "Leftmargin",
    "Linewidth",
    "Marginparwidth",
    "Newlength",
    "Pageheight",
    "Pagewidth",
    "Paperheight",
    "Paperwidth",
    "Parindent",
    "Parskip",
    "Rightmargin",
    "Setlength",
    "Settodepth",
    "Settoheight",
    "Settowidth",
    "Tabcolsep",
    "Textheight",
    "Textwidth",
    "Topmargin",
]


@Registry.add
def Newlength(name: str) -> TeX:
    return ControlSequence("newlength", (Parameter(Raw(name)),))


@Registry.add
def Setlength(name: str, value: Length | str) -> TeX:
    expr = value.expr if isinstance(value, Length) else value
    return ControlSequence("setlength", (Parameter(Raw(name)), Parameter(expr)))


@Registry.add
def Addtolength(name: str, value: Length | str) -> TeX:
    expr = value.expr if isinstance(value, Length) else value
    return ControlSequence(
        "addtolength",
        (Parameter(Raw(name)), Parameter(expr)),
    )


@Registry.add
def Settowidth(name: str, body: TeX | str) -> TeX:
    return ControlSequence(
        "settowidth",
        (Parameter(Raw(name)), Parameter(body)),
    )


@Registry.add
def Settoheight(name: str, body: TeX | str) -> TeX:
    return ControlSequence(
        "settoheight",
        (Parameter(Raw(name)), Parameter(body)),
    )


@Registry.add
def Settodepth(name: str, body: TeX | str) -> TeX:
    return ControlSequence(
        "settodepth",
        (Parameter(Raw(name)), Parameter(body)),
    )


def _const(name: str) -> Length:
    return Length(f"\\{name}")


@Registry.add
def Textwidth() -> Length:
    return _const("textwidth")


@Registry.add
def Textheight() -> Length:
    return _const("textheight")


@Registry.add
def Linewidth() -> Length:
    return _const("linewidth")


@Registry.add
def Columnwidth() -> Length:
    return _const("columnwidth")


@Registry.add
def Columnsep() -> Length:
    return _const("columnsep")


@Registry.add
def Paperwidth() -> Length:
    return _const("paperwidth")


@Registry.add
def Paperheight() -> Length:
    return _const("paperheight")


@Registry.add
def Pagewidth() -> Length:
    return _const("pagewidth")


@Registry.add
def Pageheight() -> Length:
    return _const("pageheight")


@Registry.add
def Baselineskip() -> Length:
    return _const("baselineskip")


@Registry.add
def Baselinestretch() -> Length:
    return _const("baselinestretch")


@Registry.add
def Parindent() -> Length:
    return _const("parindent")


@Registry.add
def Parskip() -> Length:
    return _const("parskip")


@Registry.add
def Topmargin() -> Length:
    return _const("topmargin")


@Registry.add
def Leftmargin() -> Length:
    return _const("leftmargin")


@Registry.add
def Rightmargin() -> Length:
    return _const("rightmargin")


@Registry.add
def Footskip() -> Length:
    return _const("footskip")


@Registry.add
def Headheight() -> Length:
    return _const("headheight")


@Registry.add
def Headsep() -> Length:
    return _const("headsep")


@Registry.add
def Marginparwidth() -> Length:
    return _const("marginparwidth")


@Registry.add
def Tabcolsep() -> Length:
    return _const("tabcolsep")


@Registry.add
def Arraystretch_len() -> Length:
    return _const("arraystretch")


@Registry.add
def Fill_len() -> Length:
    return _const("fill")


def __getattr__(name: str) -> object:
    # PyTeX renamed `Fill`, the `\fill` rubber length, to `Fill_len`. The old
    # registry key collided with `pytex_tikz.Fill`, the `\fill` path command.
    # The suffix matches `Arraystretch_len`, which avoids the `Arraystretch`
    # table command in the same way. `Fill` stays as a deprecated alias.
    if name == "Fill":
        warnings.warn(
            "pytex.commands.lengths.Fill was renamed to Fill_len to free the "
            + "'Fill' registry key for pytex_tikz.Fill; import Fill_len instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return Fill_len
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
