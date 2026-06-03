from pytex.commands.builtin import Textbf
from pytex_hsrtreport.titlepage import TitlePage, TitlePageDataLine
from pytex_hsrtreport.voting import VotingResults


def test_titlepage_wraps_in_titlepage_env():
    out = TitlePage("Title").rendered
    # The env is bracketed by the HSRTTitlePage flag toggles so footer_logo_hook
    # can suppress the footer logos on the title page only.
    assert out.startswith(r"\HSRTTitlePagetrue\begin{titlepage}")
    assert out.endswith(r"\end{titlepage}\HSRTTitlePagefalse")


def test_titlepage_renders_section_star_for_abstract():
    out = TitlePage("T", abstract="abs").rendered
    assert r"\section*{Abstract}" in out


def test_titlepage_includes_keywords():
    out = TitlePage("T", keywords="a, b, c").rendered
    assert "Keywords" in out and "a, b, c" in out


def test_titlepage_data_lines_render_in_table():
    out = TitlePage(
        "T",
        data_lines=(
            TitlePageDataLine("Autor", "Frederik"),
            TitlePageDataLine("Datum", "2026"),
        ),
    ).rendered
    assert "Autor" in out and "Frederik" in out
    assert "Datum" in out and "2026" in out


def test_titlepage_accepts_tex_value_in_data_line():
    line = TitlePageDataLine("Bold", Textbf("inner"))
    out = TitlePage("T", data_lines=(line,)).rendered
    assert r"\textbf{inner}" in out


def test_titlepage_uses_huge_big_font():
    out = TitlePage("T").rendered
    assert r"\Huge" in out


def test_titlepage_uses_blenderfont():
    out = TitlePage("T").rendered
    assert r"\blenderfont" in out


def test_titlepage_default_abstract_keywords_headings():
    out = TitlePage("T", abstract="a", keywords="k").rendered
    assert r"\section*{Abstract}" in out
    assert r"\textbf{Keywords}" in out


def test_titlepage_custom_abstract_keywords_headings():
    out = TitlePage(
        "T",
        abstract="a",
        keywords="k",
        abstract_heading="Kurzfassung",
        keywords_heading="Schlagwörter",
    ).rendered
    assert r"\section*{Kurzfassung}" in out
    assert r"\textbf{Schlagwörter}" in out
    assert r"\section*{Abstract}" not in out


def test_voting_uses_multicols():
    out = VotingResults(yes=1, no=1, abstain=0).rendered
    assert r"\begin{multicols}{3}" in out


def test_voting_uses_textbf_not_raw():
    out = VotingResults(yes=5, no=2, abstain=1).rendered
    assert r"\textbf{Ja:}" in out
    assert r"\textbf{Nein:}" in out
    assert r"\textbf{Enthaltung:}" in out


def test_voting_columnbreak_between_boxes():
    out = VotingResults(yes=1, no=1, abstain=1).rendered
    # Two columnbreaks separate the three columns
    assert out.count(r"\columnbreak") == 2


def test_voting_displays_count_strings():
    out = VotingResults(yes=42, no=7, abstain=3).rendered
    assert "42" in out and "7" in out and "3" in out
