"""Page-break penalties, length declarations and environment hooks.

Replaces the old ``pagebreaks.tex`` with native nodes. ``keeptogether``,
``protectparagraph`` and ``conditionalpagebreak`` remain TeX-level
``\\newcommand``s because they are part of the public author API the
template exposes to document writers.
"""

from pytex import (
    AtBeginEnvironment,
    AtEndEnvironment,
    BeginEnvironment,
    Command,
    EndEnvironment,
    Let,
    NewCommand,
    NewEnvironment,
    NewLength,
    Pretocmd,
    RegisterAssign,
    SetLength,
    TeX,
)
from pytex.model.raw import coerce_tex
from pytex_komascript.model import Block


def _Needspace(amount: str) -> TeX:
    return Command("needspace", amount)


def _Nopagebreak(level: int) -> TeX:
    return Command("nopagebreak", options=str(level))


def _SectionPretocmd() -> TeX:
    return Block(
        Pretocmd(
            "section",
            Block(_Needspace("\\sectionminspace"), Command("FloatBarrier")),
        ),
        Pretocmd("subsection", _Needspace("\\subsectionminspace")),
        Pretocmd("subsubsection", _Needspace("\\subsubsectionminspace")),
    )


def _LstlistingWrap() -> TeX:
    """``\\renewenvironment{lstlisting}[1][]{...}{...}`` keeping originals."""
    return Block(
        Let("originallstlisting", "lstlisting"),
        Let("endoriginallstlisting", "endlstlisting"),
        NewEnvironment(
            "lstlisting",
            Block(
                _Needspace("5\\baselineskip"),
                _Nopagebreak(4),
                Command("originallstlisting", options="#1"),
            ),
            Block(Command("endoriginallstlisting"), _Nopagebreak(3)),
            n_args=1,
            default="",
            renew=True,
        ),
    )


def _EnvHooks(name: str, *, begin_extra: TeX | None = None) -> TeX:
    return Block(
        AtBeginEnvironment(
            name,
            _Nopagebreak(4) if begin_extra is None else Block(_Nopagebreak(4), begin_extra),
        ),
        AtEndEnvironment(name, _Nopagebreak(3)),
    )


def _EnvironmentHooksBlock() -> TeX:
    return Block(
        _EnvHooks("description", begin_extra=RegisterAssign("interlinepenalty", 5000)),
        _EnvHooks("figure"),
        _EnvHooks("table"),
        _EnvHooks("verbatim", begin_extra=RegisterAssign("interlinepenalty", 10000)),
        _EnvHooks("equation"),
        _EnvHooks("align", begin_extra=RegisterAssign("interlinepenalty", 10000)),
    )


def _PenaltiesBlock() -> TeX:
    return Block(
        RegisterAssign("binoppenalty", 10000),
        RegisterAssign("relpenalty", 10000),
        RegisterAssign("brokenpenalty", 10000),
    )


def _MinSpaceLengths() -> TeX:
    return Block(
        *(NewLength(name) for name in ("sectionminspace", "subsectionminspace", "subsubsectionminspace")),
        SetLength("sectionminspace", "12\\baselineskip"),
        SetLength("subsectionminspace", "10\\baselineskip"),
        SetLength("subsubsectionminspace", "8\\baselineskip"),
    )


def _AuthorMacros() -> TeX:
    """Macros exposed to template authors (kept as ``\\newcommand``s)."""
    return Block(
        NewCommand(
            "keeptogether",
            Block(
                BeginEnvironment("minipage", "\\linewidth"),
                coerce_tex("#1"),
                EndEnvironment("minipage"),
            ),
            n_args=1,
        ),
        NewCommand(
            "protectparagraph",
            Block(
                Command("nopagebreak", options="4"),
                RegisterAssign("interlinepenalty", 10000),
            ),
        ),
        NewCommand(
            "conditionalpagebreak",
            Command("needspace", "#1"),
            n_args=1,
            default="10\\baselineskip",
        ),
    )


def PagebreaksBlock() -> TeX:
    return Block(
        _MinSpaceLengths(),
        _AuthorMacros(),
        _PenaltiesBlock(),
        _SectionPretocmd(),
        _LstlistingWrap(),
        _EnvironmentHooksBlock(),
    )


__all__ = ["PagebreaksBlock"]
