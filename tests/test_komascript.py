"""Tests for the pytex_komascript KOMA-Script extension."""

from pytex import Group, Raw, Section
from pytex_komascript import (
    Block,
    ClearPairOfPageStyles,
    IHead,
    KomaDocument,
    KomaOptions,
    Pagestyle,
    RecalcTypeArea,
    SetKomaFont,
    Subject,
)


class TestCommands:
    """Individual KOMA command serialization."""

    def test_arg_command_serialize(self):
        assert Subject(Raw("Topic")).serialize() == "\\subject{Topic}"

    def test_head_command_requires_scrlayer(self):
        cmd = IHead(Raw("left"))
        assert cmd.serialize() == "\\ihead{left}"
        assert cmd.required_packages == {"scrlayer-scrpage"}

    def test_clearpairofpagestyles(self):
        cmd = ClearPairOfPageStyles()
        assert cmd.serialize() == "\\clearpairofpagestyles"
        assert cmd.required_packages == {"scrlayer-scrpage"}

    def test_pagestyle(self):
        assert Pagestyle("scrheadings").serialize() == "\\pagestyle{scrheadings}"

    def test_setkomafont(self):
        cmd = SetKomaFont("disposition", "\\rmfamily")
        assert cmd.serialize() == "\\setkomafont{disposition}{\\rmfamily}"

    def test_komaoptions(self):
        assert KomaOptions("DIV=14").serialize() == "\\KOMAoptions{DIV=14}"

    def test_recalctypearea(self):
        assert RecalcTypeArea().serialize() == "\\recalctypearea"


class TestBlock:
    """Block emits children newline-separated without grouping braces."""

    def test_block_no_braces(self):
        block = Block(Subject(Raw("A")), Pagestyle("scrheadings"))
        out = block.serialize()
        assert out == "\\subject{A}\n\\pagestyle{scrheadings}\n"
        assert "{" not in out.replace("\\subject{A}", "").replace(
            "\\pagestyle{scrheadings}", ""
        )

    def test_block_children_exposed(self):
        sub = Subject(Raw("A"))
        block = Block(sub)
        assert block.children == (sub,)


class TestKomaDocument:
    """KomaDocument assembly."""

    def test_default_class_is_scrartcl(self):
        out = KomaDocument(content=Raw("body")).serialize()
        assert out.startswith("\\documentclass{scrartcl}")

    def test_class_options_rendered(self):
        out = KomaDocument(
            content=Raw("body"),
            font_size="11pt",
            paper_size="a4paper",
            div=12,
            bcor="10mm",
        ).serialize()
        first_line = out.splitlines()[0]
        assert first_line == (
            "\\documentclass[fontsize=11pt,a4paper,DIV=12,BCOR=10mm]{scrartcl}"
        )

    def test_twoside_and_seplines(self):
        first_line = (
            KomaDocument(
                content=Raw("body"),
                two_side=True,
                headsepline=True,
                footsepline=True,
            )
            .serialize()
            .splitlines()[0]
        )
        assert "twoside" in first_line
        assert "headsepline" in first_line
        assert "footsepline" in first_line

    def test_header_footer_adds_scrlayer_and_commands(self):
        out = KomaDocument(
            content=Raw("body"),
            head_left="L",
            head_right=Raw("R"),
            foot_center=Raw("C"),
        ).serialize()
        assert "\\usepackage{scrlayer-scrpage}" in out
        assert "\\clearpairofpagestyles" in out
        assert "\\ihead{L}" in out
        assert "\\ohead{R}" in out
        assert "\\cfoot{C}" in out
        assert "\\pagestyle{scrheadings}" in out

    def test_no_header_no_scrlayer(self):
        out = KomaDocument(content=Raw("body")).serialize()
        assert "scrlayer-scrpage" not in out
        assert "clearpairofpagestyles" not in out

    def test_sepline_pulls_scrlayer_without_fields(self):
        out = KomaDocument(content=Raw("body"), headsepline=True).serialize()
        assert "\\usepackage{scrlayer-scrpage}" in out

    def test_clear_page_styles_can_be_disabled(self):
        out = KomaDocument(
            content=Raw("body"), head_left="L", clear_page_styles=False
        ).serialize()
        assert "\\clearpairofpagestyles" not in out
        assert "\\ihead{L}" in out

    def test_koma_fonts_and_metadata(self):
        out = KomaDocument(
            content=Raw("body"),
            koma_fonts={"disposition": "\\rmfamily"},
            subject="S",
            publishers="P",
            titlehead="T",
            dedication="D",
        ).serialize()
        assert "\\setkomafont{disposition}{\\rmfamily}" in out
        assert "\\subject{S}" in out
        assert "\\publishers{P}" in out
        assert "\\titlehead{T}" in out
        assert "\\dedication{D}" in out

    def test_extra_class_options(self):
        out = KomaDocument(
            content=Raw("body"), extra_class_options=["openany", "draft"]
        ).serialize()
        first_line = out.splitlines()[0]
        assert "openany" in first_line
        assert "draft" in first_line

    def test_user_preamble_preserved(self):
        out = KomaDocument(
            content=Raw("body"),
            head_left="L",
            preamble=Raw("\\customcmd", escape_spaces=False),
        ).serialize()
        assert "\\customcmd" in out

    def test_metadata_triggers_maketitle(self):
        out = KomaDocument(content=Raw("body"), title="Title").serialize()
        assert "\\title{Title}" in out
        assert "\\maketitle" in out

    def test_document_class_override(self):
        out = KomaDocument(content=Raw("body"), document_class="scrbook").serialize()
        assert out.startswith("\\documentclass{scrbook}")

    def test_content_and_structure(self):
        doc = KomaDocument(content=Group(Section(Raw("Intro")), Raw("text")))
        out = doc.serialize()
        assert "\\begin{document}" in out
        assert "\\end{document}" in out
        assert "\\section{Intro}" in out

    def test_underlying_document_accessible(self):
        doc = KomaDocument(content=Raw("body"), font_size="12pt")
        assert doc.document.class_options == ["fontsize=12pt"]
