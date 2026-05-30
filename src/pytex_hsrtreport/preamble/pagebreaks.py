"""Page-break penalties, length declarations and environment hooks.

Replaces the old ``pagebreaks.tex`` with native nodes.
"""

from pytex import (
    AtBeginEnvironment,
    AtEndEnvironment,
    Command,
    Let,
    NewCommand,
    NewEnvironment,
    NewLength,
    Pretocmd,
    RegisterAssign,
    SetLength,
    TeX,
)
from pytex_komascript.model import Block


def _needspace(amount: str) -> TeX:
    return Command("needspace", amount)


def _nopagebreak(level: int) -> TeX:
    return Command("nopagebreak", options=str(level))


def _section_pretocmd() -> TeX:
    return Block(
        Pretocmd(
            "section",
            Block(_needspace("\\sectionminspace"), Command("FloatBarrier")),
        ),
        Pretocmd("subsection", _needspace("\\subsectionminspace")),
        Pretocmd("subsubsection", _needspace("\\subsubsectionminspace")),
    )


def _lstlisting_wrap() -> TeX:
    """``\\renewenvironment{lstlisting}[1][]{...}{...}`` keeping originals."""
    begin = Block(
        _needspace("5\\baselineskip"),
        _nopagebreak(4),
        Command("originallstlisting", options="#1"),
    )
    end = Block(Command("endoriginallstlisting"), _nopagebreak(3))
    return Block(
        Let("originallstlisting", "lstlisting"),
        Let("endoriginallstlisting", "endlstlisting"),
        NewEnvironment("lstlisting", begin, end, n_args=1, default="", renew=True),
    )


def _env_hooks(name: str, *, begin_extra: TeX | None = None) -> TeX:
    begin: TeX = _nopagebreak(4) if begin_extra is None else Block(_nopagebreak(4), begin_extra)
    return Block(
        AtBeginEnvironment(name, begin),
        AtEndEnvironment(name, _nopagebreak(3)),
    )


def _environment_hooks_block() -> TeX:
    return Block(
        _env_hooks(
            "description", begin_extra=RegisterAssign("interlinepenalty", 5000)
        ),
        _env_hooks("figure"),
        _env_hooks("table"),
        _env_hooks(
            "verbatim", begin_extra=RegisterAssign("interlinepenalty", 10000)
        ),
        _env_hooks("equation"),
        _env_hooks(
            "align", begin_extra=RegisterAssign("interlinepenalty", 10000)
        ),
    )


def _penalties_block() -> TeX:
    return Block(
        RegisterAssign("binoppenalty", 10000),
        RegisterAssign("relpenalty", 10000),
        RegisterAssign("brokenpenalty", 10000),
    )


def pagebreaks_block() -> TeX:
    return Block(
        NewLength("sectionminspace"),
        NewLength("subsectionminspace"),
        NewLength("subsubsectionminspace"),
        SetLength("sectionminspace", "12\\baselineskip"),
        SetLength("subsectionminspace", "10\\baselineskip"),
        SetLength("subsubsectionminspace", "8\\baselineskip"),
        NewCommand(
            "keeptogether",
            "\\begin{minipage}{\\linewidth}#1\\end{minipage}",
            n_args=1,
        ),
        NewCommand(
            "protectparagraph",
            "\\nopagebreak[4]\\interlinepenalty=10000",
        ),
        NewCommand(
            "conditionalpagebreak",
            "\\needspace{#1}",
            n_args=1,
            default="10\\baselineskip",
        ),
        _penalties_block(),
        _section_pretocmd(),
        _lstlisting_wrap(),
        _environment_hooks_block(),
    )


__all__ = ["pagebreaks_block"]
