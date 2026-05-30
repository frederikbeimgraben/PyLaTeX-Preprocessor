"""KOMA section styles, counter wiring and chapter-mark indirection."""

from pytex import (
    CounterWithin,
    CounterWithout,
    IncludeTeX,
    NewCommand,
    RenewCommand,
    SetLength,
    TeX,
)
from pytex_komascript import RedeclareSectionCommand, SetKomaFont
from pytex_komascript.model import Block

from ..paths import TEX_DIR


def sections_block() -> TeX:
    return Block(
        SetKomaFont("disposition", "\\blenderfont\\bfseries"),
        SetKomaFont("chapter", "\\LARGE\\blenderfont\\bfseries"),
        SetKomaFont("section", "\\Large\\blenderfont\\bfseries"),
        SetKomaFont("subsection", "\\large\\blenderfont\\bfseries"),
        SetKomaFont("subsubsection", "\\large\\blenderfont\\bfseries"),
        IncludeTeX(TEX_DIR / "sections_marks.tex"),
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
        NewCommand("decoRule", "\\rule{.8\\textwidth}{.4pt}"),
        CounterWithin("figure", "chapter"),
        CounterWithin("table", "chapter"),
        CounterWithout("equation", "chapter"),
        RenewCommand("thefigure", "\\thechapter.\\arabic{figure}"),
        RenewCommand("thetable", "\\thechapter.\\arabic{table}"),
    )


__all__ = ["sections_block"]
