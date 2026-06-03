from pytex_components.citations import Fcite
from pytex_components.cleveref_names import GermanCrefNames
from pytex_components.pagebreak import (
    Conditionalpagebreak,
    Keeptogether,
    Smartsection,
    Smartsubsection,
)
from pytex_components.wordcount import WordcountCommands
from pytex_hsrtreport.colors import HSRT_PALETTE, HSRTColors
from pytex_hsrtreport.glossary import AcrShortcut, HSRTGlossarySetup
from pytex_hsrtreport.hyperref_config import HSRTHyperref
from pytex_hsrtreport.listings import HSRTListingStyles, style_options
from pytex_hsrtreport.logos import Logo, LogoStrip, logo_path
from pytex_hsrtreport.titlepage import TitlePage, TitlePageDataLine
from pytex_hsrtreport.variants import Variant


def test_hsrt_palette_size():
    assert len(HSRT_PALETTE) >= 7


def test_hsrt_colors_renders_definecolor_per_entry():
    out = HSRTColors().rendered
    for name in HSRT_PALETTE:
        assert f"definecolor{{{name}}}" in out


def test_german_cref_names_emits_pairs():
    out = GermanCrefNames().rendered
    assert "crefname{figure}{Abbildung}{Abbildungen}" in out
    assert "Crefname{figure}{Abbildung}{Abbildungen}" in out


def test_hsrt_hyperref_brand_colors():
    out = HSRTHyperref().rendered
    assert "colorlinks=true" in out
    assert "citecolor=hsrtcite" in out
    assert "linkcolor=hsrtlink" in out
    assert "urlcolor=hsrturl" in out


def test_glossary_setup_renders():
    out = HSRTGlossarySetup().rendered
    assert "makeglossaries" in out
    assert "manualfixedwidth" in out
    assert "Wort/Abk" in out


def test_acr_shortcut():
    assert AcrShortcut().rendered == r"\newcommand{\acr}{\acrshort}"


def test_listing_styles():
    out = HSRTListingStyles().rendered
    for s in ("htmlCode", "phpCode", "jsCode", "shellCode", "shellCodeNOPASSWD", "URL"):
        assert f"lstdefinestyle{{{s}}}" in out


def test_style_options_lookup():
    opts = style_options("htmlCode")
    assert opts["language"] == "html"


def test_logo_renders_includegraphics():
    out = Logo("HSRT", inline_base64=False).rendered
    assert "includegraphics" in out and "HSRT.pdf" in out


def test_logo_unknown_raises():
    import pytest

    with pytest.raises(ValueError):
        Logo("DOES_NOT_EXIST", inline_base64=False)


def test_logo_strip_renders_each():
    out = LogoStrip(("HSRT", "INF"), inline_base64=False).rendered
    assert "HSRT.pdf" in out and "INF.pdf" in out
    assert "\\hspace{0.5cm}" in out


def test_logo_path_lookup():
    p = logo_path("INF")
    assert p.name == "INF.pdf"


def test_variants_default_logos_inf():
    from pytex_hsrtreport.variants import default_logo_names

    assert default_logo_names(Variant.INF) == ("INF",)


def test_titlepage_basic_render():
    tp = TitlePage(
        title="A Title",
        abstract="abs",
        keywords="kw1, kw2",
        data_lines=(TitlePageDataLine("Autor", "Frederik"),),
    )
    out = tp.rendered
    assert "begin{titlepage}" in out
    assert "A Title" in out
    assert "abs" in out
    assert "kw1, kw2" in out
    assert "Autor" in out and "Frederik" in out


def test_pagebreak_keeptogether():
    out = Keeptogether("body").rendered
    assert out == r"\begin{minipage}{\linewidth}body\end{minipage}"


def test_conditional_pagebreak_default():
    assert Conditionalpagebreak().rendered == r"\needspace{10\baselineskip}"


def test_smartsection_with_short():
    out = Smartsection("Long", short="S").rendered
    assert "needspace{\\sectionminspace}" in out
    assert "section[S]{Long}" in out


def test_smartsubsection():
    out = Smartsubsection("Sub").rendered
    assert "needspace{\\subsectionminspace}" in out
    assert "subsection{Sub}" in out


def test_fcite_renders_hyperlink():
    out = Fcite("knuth1984").rendered
    assert r"\hyperlink{cite.0@knuth1984}" in out
    assert "citeauthor{knuth1984}" in out
    assert "citeyear{knuth1984}" in out


def test_wordcount_commands():
    out = WordcountCommands().rendered
    assert "\\quickwordcount" in out
    assert "\\detailtexcount" in out
    assert "texcount" in out
