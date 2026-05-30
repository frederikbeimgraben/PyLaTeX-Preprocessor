"""Header / footer fields. Uses @-letter (``page_setup.tex``)."""

from pytex import IncludeTeX, SetLength, TeX
from pytex_komascript import ClearPairOfPageStyles, Pagestyle, SetKomaFont
from pytex_komascript.model import Block

from ..paths import TEX_DIR


def page_setup_block() -> TeX:
    return Block(
        ClearPairOfPageStyles(),
        SetKomaFont("pageheadfoot", "\\color{gray}\\blenderfont"),
        SetKomaFont("pagenumber", "\\color{gray}\\blenderfont"),
        SetLength("footskip", "35pt"),
        IncludeTeX(TEX_DIR / "page_setup.tex"),
        Pagestyle("scrheadings"),
    )


__all__ = ["page_setup_block"]
