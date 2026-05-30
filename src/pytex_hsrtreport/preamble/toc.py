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


def _toc_block() -> TeX:
    """All toc tweaks wrapped in a single ``\\makeatletter`` group."""
    return MakeAtLetter(
        Block(
            Pretocmd("addchaptertocentry", Command("needspace", "8\\baselineskip")),
            Apptocmd("addchaptertocentry", Command("nopagebreak", options="4")),
            AtBeginEnvironment(
                "toc",
                Block(
                    RegisterAssign("clubpenalty", 10000),
                    RegisterAssign("widowpenalty", 10000),
                    RegisterAssign("interlinepenalty", 500),
                ),
            ),
            Pretocmd(
                "addsectiontocentry",
                Block(Command("penalty"), coerce_tex("-500")),
            ),
            Pretocmd("addsubsectiontocentry", Command("nopagebreak", options="3")),
            RenewCommand(
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
            ),
        )
    )


def toc_config_block() -> TeX:
    return _toc_block()


__all__ = ["toc_config_block"]
