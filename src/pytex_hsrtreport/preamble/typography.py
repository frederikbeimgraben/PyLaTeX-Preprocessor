"""Typography: baseline stretch, lstset overlay, penalties — all native."""

from pytex import (
    AtBeginEnvironment,
    AtEndEnvironment,
    BeginEnvironment,
    Command,
    EndEnvironment,
    MakeAtLetter,
    NewEnvironment,
    RegisterAssign,
    RenewCommand,
    SetCounter,
    SetLength,
    TeX,
)
from pytex.library.listings import LstSet
from pytex_komascript.model import Block


def _PenaltiesAndSpacing() -> TeX:
    return Block(
        RegisterAssign("hyphenpenalty", 500),
        RegisterAssign("exhyphenpenalty", 500),
        RegisterAssign("tolerance", 1000),
        RegisterAssign("emergencystretch", "3em"),
        RegisterAssign("spaceskip", "0.3em plus 0.2em minus 0.1em"),
        RegisterAssign("xspaceskip", "0.6em plus 0.3em minus 0.15em"),
        RegisterAssign("widowpenalty", 10000),
        RegisterAssign("clubpenalty", 10000),
        RegisterAssign("displaywidowpenalty", 10000),
        MakeAtLetter(
            Block(
                RegisterAssign("@beginparpenalty", 10000),
                RegisterAssign("@endparpenalty", 10000),
            )
        ),
        Command("raggedbottom"),
        Command("flushbottom"),
        RegisterAssign("interlinepenalty", 150),
        RegisterAssign("predisplaypenalty", 10000),
        RegisterAssign("postdisplaypenalty", 10000),
        RegisterAssign("floatingpenalty", 20000),
        RegisterAssign("parfillskip", "0pt plus 1fil"),
    )


def _ProtectedList(env_name: str, list_env: str) -> TeX:
    return NewEnvironment(
        env_name,
        Block(BeginEnvironment("minipage", "\\linewidth"), BeginEnvironment(list_env)),
        Block(EndEnvironment(list_env), EndEnvironment("minipage")),
    )


def _ProtectedLists() -> TeX:
    return Block(
        _ProtectedList("protecteditemize", "itemize"),
        _ProtectedList("protectedenumerate", "enumerate"),
    )


def _ListHook(name: str, *, ip: int) -> TeX:
    return Block(
        AtBeginEnvironment(
            name,
            Block(Command("nopagebreak", options="4"), RegisterAssign("interlinepenalty", ip)),
        ),
        AtEndEnvironment(name, Command("nopagebreak", options="3")),
    )


def _ListHooks() -> TeX:
    return Block(*(_ListHook(n, ip=5000) for n in ("itemize", "enumerate")))


def _NosepList(env_name: str, list_env: str) -> TeX:
    return NewEnvironment(
        env_name,
        BeginEnvironment(list_env, options="nosep,leftmargin=*"),
        EndEnvironment(list_env),
    )


def _ListenAbsatz() -> TeX:
    return Block(
        _NosepList("listenabsatz", "itemize"),
        _NosepList("listenabsatz*", "enumerate"),
    )


def _TypographyNative() -> TeX:
    return Block(
        _PenaltiesAndSpacing(),
        _ProtectedLists(),
        _ListHooks(),
        _ListenAbsatz(),
    )


def TypographyBlock() -> TeX:
    return Block(
        RenewCommand("baselinestretch", "1.5"),
        SetLength("parskip", "0.5em plus 0.2em minus 0.1em"),
        SetLength("parindent", "0pt"),
        LstSet(
            {
                "float": "H",
                "belowskip": "-0.5em plus 0.2em",
                "aboveskip": "0.5em plus 0.2em",
                "keepspaces": True,
                "breaklines": True,
            }
        ),
        _TypographyNative(),
        RenewCommand("floatpagefraction", "0.8"),
        RenewCommand("topfraction", "0.9"),
        RenewCommand("bottomfraction", "0.9"),
        RenewCommand("textfraction", "0.1"),
        SetCounter("topnumber", 2),
        SetCounter("bottomnumber", 2),
        SetCounter("totalnumber", 4),
    )


__all__ = ["TypographyBlock"]
