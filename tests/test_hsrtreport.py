"""Tests for the pytex_hsrtreport package."""

from pytex import AcronymEntry, Acronyms, Glossary, GlossaryEntry, Group, Raw, Section
from pytex_hsrtreport import (
    CustomBox,
    HSRTReport,
    InfoBox,
    SuccessBox,
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
        # Per-logo tikz nodes are baked from Python with absolute PDF paths
        # and pixel-cm heights computed at build time. The exact path depends
        # on where pytex_hsrtreport is installed, so we look for the suffix.
        out = _serialize(variant="INF_meti")
        assert "Images/Logos/INF/Kombiniert.pdf}" in out
        assert "Images/Logos/HSRT.pdf}" in out
        # Default logo scale is 0.9, global 1.0 -> 1.5 × 0.9 × 1.0 = 1.35cm.
        assert "height=1.35cm" in out

    def test_footer_logos_toggle(self):
        # The footer-logo nodes are emitted by Python only when footer_logos
        # is true; the xshift=-1.5cm anchor is unique to the footer strip.
        marker = "xshift=-1.5cm, yshift=2pt"
        assert marker in _serialize(footer_logos=True)
        assert marker not in _serialize(footer_logos=False)

    def test_watermark(self):
        # The watermark text is baked directly into the DraftwatermarkOptions
        # body; no \waterMarkText TeX define is emitted.
        out = _serialize(watermark="DRAFT")
        assert "DRAFT~~" in out
        assert "\\DraftwatermarkOptions{" in out

    def test_no_watermark_text_define(self):
        # Even when set, the text is inlined — no separate command exists.
        out = _serialize(watermark="DRAFT")
        assert "\\newcommand{\\waterMarkText}" not in out

    def test_preamble_blocks_present(self):
        out = _serialize()
        for needle in (
            "\\usepackage[ngerman]{babel}",
            "\\hypersetup{",
            "\\setkomafont{disposition}",
            "\\definecolor{hanblue}",
            "\\DraftwatermarkOptions{",
            "\\makeatletter",
        ):
            assert needle in out, needle

    def test_no_coloredbox_env_defined(self):
        # ColoredBox is no longer a TeX environment — it is a Python type that
        # emits its contents inline.
        out = _serialize()
        assert "\\NewEnviron{ColoredBox}" not in out
        assert "\\NewEnviron{InfoBox}" not in out


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
        # ColoredBox emits its mdframed contents inline — no environment.
        out = InfoBox(Raw("hi")).serialize()
        assert "\\begin{ColoredBox}" not in out
        assert "\\begin{mdframed}" in out
        assert "\\faInfoCircle" in out
        # Default nesting level=1 -> bg 12%, icon 32%.
        assert "{blue!12}" in out
        assert "{blue!32}" in out

    def test_warningbox(self):
        out = WarningBox(Raw("x")).serialize()
        assert "\\faExclamationTriangle" in out
        assert "{red!12}" in out
        assert "{red!32}" in out

    def test_successbox_offset_y(self):
        # SuccessBox bumps icon_offset_y to 2pt.
        out = SuccessBox(Raw("x")).serialize()
        assert "\\faCheckCircle" in out
        assert "2pt-0.7cm" in out  # SuccessBox icon_offset_y=2pt

    def test_custombox_args(self):
        out = CustomBox(Raw("x"), "\\faStar", "blue").serialize()
        assert "\\faStar" in out
        assert "{blue!12}" in out

    def test_voting_results_yes_wins(self):
        out = VotingResults(Raw("Antrag"), 5, 2, 1).serialize()
        assert "\\faVoteYea" in out
        assert "{britishracinggreen!12}" in out  # yes > no
        assert "\\textbf{Ja:} 5" in out
        assert "\\textbf{Nein:} 2" in out
        assert "\\textbf{Enthaltung:} 1" in out

    def test_voting_results_no_wins(self):
        out = VotingResults(Raw("Antrag"), 1, 5, 2).serialize()
        assert "{red!12}" in out

    def test_voting_results_tie(self):
        out = VotingResults(Raw("Antrag"), 3, 3, 1).serialize()
        assert "{eggplant!12}" in out

    def test_nested_coloredbox_bumps_opacity(self):
        # Inner ColoredBox at level=2 -> bg=round((0.05 + 0.075*2)*100) = 20.
        outer = InfoBox(WarningBox(Raw("inner")))
        out = outer.serialize()
        assert "{blue!12}" in out  # outer at L=1
        assert "{red!20}" in out  # inner at L=2

    def test_coloredbox_required_packages(self):
        pkgs = InfoBox(Raw("hi")).required_packages
        assert any(
            (p if isinstance(p, str) else p.name) == "mdframed" for p in pkgs
        )
        assert any(
            (p if isinstance(p, str) else p.name) == "fontawesome5" for p in pkgs
        )


class TestWordCount:
    def test_count_simple(self):
        assert count_words(Raw("one two three", escape_spaces=False)) == 3

    def test_strips_latex(self):
        node = Group(Section(Raw("Title")), Raw("\\textbf{bold} and text", escape_spaces=False))
        # "Title" + "bold and text" -> Title bold and text = 4 words
        assert count_words(node) == 4

    def test_content_text_strips_math(self):
        assert "x" not in content_text(Raw("before $x^2$ after", escape_spaces=False)).split()
