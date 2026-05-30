"""KOMA section styles, counter wiring and chapter-mark indirection."""

from pytex import (
    Command,
    CounterWithin,
    CounterWithout,
    Def,
    Let,
    RenewCommand,
    SetLength,
    TeX,
)
from pytex_komascript import RedeclareSectionCommand, SetKomaFont
from pytex_komascript.model import Block

_MARK_NAMES: tuple[tuple[str, str], ...] = (
    ("Chapter", "chapter"),
    ("Section", "section"),
    ("Subsection", "subsection"),
    ("Subsubsection", "subsubsection"),
)


def _MarkIndirection(capital: str, lower: str) -> TeX:
    """``\\let\\<C>mark\\<l>mark`` + redefined mark that captures the name."""
    return Block(
        Let(f"{capital}mark", f"{lower}mark"),
        Def(
            f"{lower}mark",
            Block(
                Def(f"{capital}name", "#1"),
                Command(f"{capital}mark", "#1"),
            ),
            param_text="#1",
        ),
    )


def _SectionMarksBlock() -> TeX:
    return Block(*(_MarkIndirection(c, l) for c, l in _MARK_NAMES))


def SectionsBlock() -> TeX:
    return Block(
        SetKomaFont("disposition", "\\blenderfont\\bfseries"),
        SetKomaFont("chapter", "\\LARGE\\blenderfont\\bfseries"),
        SetKomaFont("section", "\\Large\\blenderfont\\bfseries"),
        SetKomaFont("subsection", "\\large\\blenderfont\\bfseries"),
        SetKomaFont("subsubsection", "\\large\\blenderfont\\bfseries"),
        _SectionMarksBlock(),
        RedeclareSectionCommand(
            "chapter",
            "beforeskip=3ex plus 1ex minus 0.5ex,afterskip=1.5ex plus 0.3ex,style=section",
        ),
        RedeclareSectionCommand(
            "section",
            "beforeskip=4.5ex plus 1.5ex minus 0.5ex,afterskip=1.5ex plus 0.3ex",
        ),
        RedeclareSectionCommand(
            "subsection",
            "beforeskip=3.5ex plus 1ex minus 0.5ex,afterskip=1ex plus 0.2ex",
        ),
        RedeclareSectionCommand(
            "subsubsection",
            "beforeskip=2ex plus 0.5ex minus 0.3ex,afterskip=0.8ex plus 0.1ex",
        ),
        SetLength("parskip", "0.8ex plus 0.2ex minus 0.1ex"),
        CounterWithin("figure", "chapter"),
        CounterWithin("table", "chapter"),
        CounterWithout("equation", "chapter"),
        RenewCommand("thefigure", "\\thechapter.\\arabic{figure}"),
        RenewCommand("thetable", "\\thechapter.\\arabic{table}"),
    )


__all__ = ["SectionsBlock"]
