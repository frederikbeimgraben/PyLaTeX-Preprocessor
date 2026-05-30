"""Typography: baseline stretch, lstset overlay, penalties — all native."""

from pytex import (
    AtBeginEnvironment,
    AtEndEnvironment,
    Command,
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


def _penalties_and_spacing() -> TeX:
    """All bare register assignments from the old ``typography.tex``."""
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


def _protected_lists() -> TeX:
    return Block(
        NewEnvironment(
            "protecteditemize",
            "\\begin{minipage}{\\linewidth}\\begin{itemize}",
            "\\end{itemize}\\end{minipage}",
        ),
        NewEnvironment(
            "protectedenumerate",
            "\\begin{minipage}{\\linewidth}\\begin{enumerate}",
            "\\end{enumerate}\\end{minipage}",
        ),
    )


def _list_hooks() -> TeX:
    return Block(
        AtBeginEnvironment(
            "itemize",
            Block(
                Command("nopagebreak", options="4"),
                RegisterAssign("interlinepenalty", 5000),
            ),
        ),
        AtEndEnvironment("itemize", Command("nopagebreak", options="3")),
        AtBeginEnvironment(
            "enumerate",
            Block(
                Command("nopagebreak", options="4"),
                RegisterAssign("interlinepenalty", 5000),
            ),
        ),
        AtEndEnvironment("enumerate", Command("nopagebreak", options="3")),
    )


def _listenabsatz() -> TeX:
    return Block(
        NewEnvironment(
            "listenabsatz",
            "\\begin{itemize}[nosep,leftmargin=*]",
            "\\end{itemize}",
        ),
        NewEnvironment(
            "listenabsatz*",
            "\\begin{enumerate}[nosep,leftmargin=*]",
            "\\end{enumerate}",
        ),
    )


def _typography_native() -> TeX:
    """Native replacement for the old ``typography.tex``."""
    return Block(
        _penalties_and_spacing(),
        _protected_lists(),
        _list_hooks(),
        _listenabsatz(),
    )


def typography_block() -> TeX:
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
        _typography_native(),
        RenewCommand("floatpagefraction", "0.8"),
        RenewCommand("topfraction", "0.9"),
        RenewCommand("bottomfraction", "0.9"),
        RenewCommand("textfraction", "0.1"),
        SetCounter("topnumber", 2),
        SetCounter("bottomnumber", 2),
        SetCounter("totalnumber", 4),
    )


__all__ = ["typography_block"]
