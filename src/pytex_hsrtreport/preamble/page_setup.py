"""Layout / header / footer config for the HSRT report."""

from pytex import (
    Command,
    Ifnum,
    IfUndefined,
    MakeAtLetter,
    SetLength,
    TeX,
)
from pytex.model.raw import coerce_tex
from pytex_komascript import ClearPairOfPageStyles, Pagestyle, SetKomaFont
from pytex_komascript.model import Block


def _WriteLastpageAux() -> TeX:
    """``\\AtEndDocument{\\immediate\\write\\@auxout{\\gdef\\@lastpage{\\thepage}}}``.

    Wrapped in :class:`MakeAtLetter` so the ``@`` letters tokenise.
    Use raw LaTeX to avoid expansion issues with ImmediateWrite.
    """
    from pytex import Raw

    return MakeAtLetter(
        Raw(
            r"\AtEndDocument{\immediate\write\@auxout{\string\gdef\string\@lastpage{\thepage}}}",
            escape_spaces=False,
            safe=False,
        )
    )


def _ChapterOnly(body: TeX) -> TeX:
    """``\\ifnum\\value{chapter}>0\\relax body\\fi`` wrapper."""
    return Ifnum("\\value{chapter}>0", body)


def _OheadStarBody() -> TeX:
    return _ChapterOnly(
        Block(
            Command("Roman", Command("thechapter")),
            coerce_tex("~–~"),
            Command("Chaptername"),
        )
    )


def _CfootBody() -> TeX:
    return _ChapterOnly(
        Block(
            coerce_tex("Seite~"),
            Command("thepage"),
            MakeAtLetter(
                IfUndefined(
                    "@lastpage",
                    "",
                    Block(coerce_tex("~von~"), Command("@lastpage")),
                )
            ),
        )
    )


def _OheadBody() -> TeX:
    return _ChapterOnly(
        Block(
            Command("thechapter"),
            coerce_tex("~–~"),
            Command("Chaptername"),
        )
    )


def _HeaderFooterBlock() -> TeX:
    return Block(
        _WriteLastpageAux(),
        Command("ohead*", _OheadStarBody()),
        MakeAtLetter(Command("ifoot", Command("@author"))),
        Command("cfoot", _CfootBody()),
        Command("ohead", _OheadBody()),
        MakeAtLetter(Command("ihead", Command("@title"))),
    )


def PageSetupBlock() -> TeX:
    return Block(
        ClearPairOfPageStyles(),
        SetKomaFont("pageheadfoot", "\\color{gray}\\blenderfont"),
        SetKomaFont("pagenumber", "\\color{gray}\\blenderfont"),
        SetLength("footskip", "35pt"),
        _HeaderFooterBlock(),
        Pagestyle("scrheadings"),
    )


__all__ = ["PageSetupBlock"]
