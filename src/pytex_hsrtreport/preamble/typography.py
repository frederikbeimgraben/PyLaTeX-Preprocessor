"""Typography: baseline stretch, lstset overlay, penalties (in ``typography.tex``)."""

from pytex import (
    IncludeTeX,
    RenewCommand,
    SetCounter,
    SetLength,
    TeX,
)
from pytex.library.listings import LstSet
from pytex_komascript.model import Block

from ..paths import TEX_DIR


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
        IncludeTeX(TEX_DIR / "typography.tex"),
        RenewCommand("floatpagefraction", "0.8"),
        RenewCommand("topfraction", "0.9"),
        RenewCommand("bottomfraction", "0.9"),
        RenewCommand("textfraction", "0.1"),
        SetCounter("topnumber", 2),
        SetCounter("bottomnumber", 2),
        SetCounter("totalnumber", 4),
    )


__all__ = ["typography_block"]
