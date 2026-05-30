"""Header / footer fields — built natively, no @-letter Raw."""

from pytex import (
    AtEndDocument,
    Command,
    IfUndefined,
    Ifnum,
    ImmediateWrite,
    MakeAtLetter,
    SetLength,
    TeX,
)
from pytex.model.raw import coerce_tex
from pytex_komascript import ClearPairOfPageStyles, Pagestyle, SetKomaFont
from pytex_komascript.model import Block


def _write_lastpage_aux() -> TeX:
    """``\\AtEndDocument{\\immediate\\write\\@auxout{\\gdef\\@lastpage{\\thepage}}}``.

    Wrapped in :class:`MakeAtLetter` so the ``@`` letters tokenise.
    """
    return MakeAtLetter(
        AtEndDocument(
            ImmediateWrite(
                "@auxout",
                Block(
                    Command("string", Command("gdef")),
                    Command("string", Command("@lastpage")),
                    coerce_tex("{"),
                    Command("thepage"),
                    coerce_tex("}"),
                ),
            )
        )
    )


def _chapter_only(body: TeX) -> TeX:
    """``\\ifnum\\value{chapter}>0\\relax body\\fi`` wrapper."""
    return Ifnum("\\value{chapter}>0", body)


def _ohead_star_body() -> TeX:
    return _chapter_only(
        Block(
            Command("Roman", Command("thechapter")),
            coerce_tex("~–~"),
            Command("Chaptername"),
        )
    )


def _cfoot_body() -> TeX:
    return _chapter_only(
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


def _ohead_body() -> TeX:
    return _chapter_only(
        Block(
            Command("thechapter"),
            coerce_tex("~–~"),
            Command("Chaptername"),
        )
    )


def _header_footer_block() -> TeX:
    """KOMA header / footer commands (replaces the old ``page_setup.tex``)."""
    return Block(
        _write_lastpage_aux(),
        Command("ohead*", _ohead_star_body()),
        MakeAtLetter(Command("ifoot", Command("@author"))),
        Command("cfoot", _cfoot_body()),
        Command("ohead", _ohead_body()),
        MakeAtLetter(Command("ihead", Command("@title"))),
    )


def page_setup_block() -> TeX:
    return Block(
        ClearPairOfPageStyles(),
        SetKomaFont("pageheadfoot", "\\color{gray}\\blenderfont"),
        SetKomaFont("pagenumber", "\\color{gray}\\blenderfont"),
        SetLength("footskip", "35pt"),
        _header_footer_block(),
        Pagestyle("scrheadings"),
    )


__all__ = ["page_setup_block"]
