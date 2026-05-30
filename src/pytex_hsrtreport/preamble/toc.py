"""Table-of-contents tweaks — native, uses ``\\@dottedtocline`` inside MakeAtLetter."""

from pytex import (
    Apptocmd,
    AtBeginEnvironment,
    Command,
    MakeAtLetter,
    Pretocmd,
    RegisterAssign,
    RenewCommand,
    TeX,
)
from pytex.model.raw import coerce_tex
from pytex_komascript.model import Block


def _TocPenalties() -> TeX:
    return Block(
        RegisterAssign("clubpenalty", 10000),
        RegisterAssign("widowpenalty", 10000),
        RegisterAssign("interlinepenalty", 500),
    )


def _LstlistingTocEntry() -> TeX:
    return RenewCommand(
        "l@lstlisting",
        Command(
            "@dottedtocline",
            "1",
            "1em",
            "2.3em",
            Block(Command("blenderfont"), coerce_tex("#1")),
            Block(Command("blenderfont"), coerce_tex("#2")),
        ),
        n_args=2,
    )


def TocConfigBlock() -> TeX:
    """All toc tweaks wrapped in a single ``\\makeatletter`` group."""
    return MakeAtLetter(
        Block(
            Pretocmd("addchaptertocentry", Command("needspace", "8\\baselineskip")),
            Apptocmd("addchaptertocentry", Command("nopagebreak", options="4")),
            AtBeginEnvironment("toc", _TocPenalties()),
            Pretocmd(
                "addsectiontocentry",
                Block(Command("penalty"), coerce_tex("-500")),
            ),
            Pretocmd("addsubsectiontocentry", Command("nopagebreak", options="3")),
            _LstlistingTocEntry(),
        )
    )


__all__ = ["TocConfigBlock"]
