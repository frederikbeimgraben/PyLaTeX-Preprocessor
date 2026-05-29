"""Tests for the pytex_hsrtreport package."""

from pytex import AcronymEntry, Acronyms, Glossary, GlossaryEntry, Group, Raw, Section
from pytex_hsrtreport import (
    CustomBox,
    HSRTReport,
    InfoBox,
    VotingResults,
    WarningBox,
    content_text,
    count_words,
    resolve_logos,
)


def _serialize(**kwargs) -> str:
    return HSRTReport(content=Raw("body", escape_spaces=False), **kwargs).serialize()


class TestVariantsLogos:
    def test_inf_default_logos(self):
        assert resolve_logos("INF_meti") == [("INF/Kombiniert", 0.9), ("HSRT", 0.9)]

    def test_stupa_default(self):
        names = [n for n, _ in resolve_logos("STUPA")]
        assert names[0] == "STUPA/Black"

    def test_logos_override(self):
        assert resolve_logos("INF_meti", {"HSRT": 1.0}) == [("HSRT", 1.0)]

    def test_override_set(self):
        assert resolve_logos("INF_meti", ["HSRT"]) == [("HSRT", 0.9)]


class TestDocumentStructure:
    def test_scrbook_class(self):
        out = _serialize()
        assert out.startswith("\\documentclass[")
        assert "{scrbook}" in out.splitlines()[0]

    def test_class_options(self):
        first = _serialize(font_size="12pt", paper_size="a4", div=14).splitlines()[0]
        assert "fontsize=12pt" in first
        assert "paper=a4" in first
        assert "DIV=14" in first
        assert "onecolumn" in first
        assert "oneside" in first

    def test_twoside(self):
        first = _serialize(two_side=True).splitlines()[0]
        assert "twoside" in first
        assert "oneside" not in first

    def test_begin_end_document(self):
        out = _serialize()
        assert "\\begin{document}" in out
        assert "\\end{document}" in out

    def test_no_duplicate_maketitle_in_body(self):
        out = _serialize(title="T", author="A")
        # \maketitle only in the renewcommand definition and AtBeginDocument hook
        assert out.count("\\maketitle") == 2

    def test_logos_emitted(self):
        out = _serialize(variant="INF_meti")
        assert "\\AddLogo{INF/Kombiniert}{0.9}" in out
        assert "\\AddLogo{HSRT}{0.9}" in out

    def test_footer_logos_toggle(self):
        # The footer logo loop is wrapped in \ifdefstring{\istitlepage}; the
        # title-page logo loop is not, so this marker is footer-only.
        marker = "\\ifdefstring{\\istitlepage}{\\true}{}{"
        assert marker in _serialize(footer_logos=True)
        assert marker not in _serialize(footer_logos=False)

    def test_watermark(self):
        out = _serialize(watermark="DRAFT")
        assert "\\newcommand{\\waterMarkText}{DRAFT}" in out

    def test_preamble_blocks_present(self):
        out = _serialize()
        for needle in (
            "\\usepackage[ngerman]{babel}",
            "\\hypersetup{",
            "\\setkomafont{disposition}",
            "\\definecolor{hanblue}",
            "blstlisting",
            "\\NewEnviron{InfoBox}",
            "\\DraftwatermarkOptions{",
            "\\makeatletter",
        ):
            assert needle in out, needle


class TestToggles:
    def test_toc(self):
        assert "\\tableofcontents" in _serialize(toc=True)
        assert "\\tableofcontents" not in _serialize(toc=False)

    def test_glossary(self):
        out = _serialize(
            glossary=Glossary(GlossaryEntry("tk", "Textkörper", "Bereich"))
        )
        assert "\\newglossaryentry{tk}" in out
        assert "\\printglossary" in out

    def test_acronyms(self):
        out = _serialize(acronyms=Acronyms(AcronymEntry("MPG", "MPG", "Gesetz")))
        assert "\\newacronym{MPG}" in out
        assert "type=\\acronymtype" in out

    def test_bibliography(self):
        out = _serialize(bibliography="Main.bib", bibliography_backend="biber")
        assert "backend=biber" in out
        assert "\\addbibresource{Main.bib}" in out
        assert "\\makebib" in out

    def test_no_bibliography(self):
        assert "biblatex" not in _serialize()

    def test_wordcount_line(self):
        doc = HSRTReport(
            content=Raw("one two three four five", escape_spaces=False),
            wordcount=True,
        )
        out = doc.serialize()
        assert "\\AddTitlePageDataLine{Wortanzahl}{5}" in out


class TestInfoBoxes:
    def test_infobox(self):
        out = InfoBox(Raw("hi")).serialize()
        assert out.startswith("\\begin{InfoBox}")
        assert out.endswith("\\end{InfoBox}")

    def test_infobox_options(self):
        out = InfoBox(Raw("hi"), options="background.color={red}").serialize()
        assert "\\begin{InfoBox}[background.color={red}]" in out

    def test_warningbox(self):
        assert "\\begin{WarningBox}" in WarningBox(Raw("x")).serialize()

    def test_custombox_args(self):
        out = CustomBox(Raw("x"), "\\faStar", "blue").serialize()
        assert out.startswith("\\begin{CustomBox}{\\faStar}{blue}")

    def test_voting_results(self):
        out = VotingResults(Raw("Antrag"), 5, 2, 1).serialize()
        assert out.startswith("\\begin{VotingResults}{5}{2}{1}")


class TestWordCount:
    def test_count_simple(self):
        assert count_words(Raw("one two three", escape_spaces=False)) == 3

    def test_strips_latex(self):
        node = Group(Section(Raw("Title")), Raw("\\textbf{bold} and text", escape_spaces=False))
        # "Title" + "bold and text" -> Title bold and text = 4 words
        assert count_words(node) == 4

    def test_content_text_strips_math(self):
        assert "x" not in content_text(Raw("before $x^2$ after", escape_spaces=False)).split()
