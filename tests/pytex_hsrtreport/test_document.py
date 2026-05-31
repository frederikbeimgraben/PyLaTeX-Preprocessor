import pytest

from pytex.commands.builtin import Section
from pytex_hsrtreport import HSRTReport, Variant


def test_default_class_is_scrbook():
    doc = HSRTReport(Section("Hi"))
    assert doc.document_class == "scrbook"


def test_rejects_non_scrbook():
    with pytest.raises(ValueError):
        HSRTReport(Section("Hi"), document_class="scrartcl")


def test_preamble_has_hsrt_colors():
    out = HSRTReport(Section("Hi")).rendered
    for col in (
        "britishracinggreen",
        "eggplant",
        "hanblue",
        "navyblue",
        "pansypurple",
        "shockingpink",
    ):
        assert col in out


def test_preamble_has_cleveref_names_de():
    out = HSRTReport(Section("Hi")).rendered
    assert "Abbildung" in out
    assert "Tabelle" in out
    assert "Gleichung" in out


def test_preamble_has_listing_styles():
    out = HSRTReport(Section("Hi")).rendered
    assert "lstdefinestyle{htmlCode}" in out
    assert "lstdefinestyle{phpCode}" in out
    assert "lstdefinestyle{shellCode}" in out


def test_glossary_setup_opt_in():
    out_off = HSRTReport(Section("Hi"), show_glossary=False, show_acronyms=False).rendered
    out_on = HSRTReport(Section("Hi"), show_glossary=True).rendered
    assert "makeglossaries" not in out_off
    assert "makeglossaries" in out_on


def test_hyperref_with_brand_colors():
    out = HSRTReport(Section("Hi")).rendered
    assert "hypersetup" in out
    assert "linkcolor=hsrtlink" in out
    # color walker emits \definecolor for the named HSRT colours
    assert "definecolor{hsrtlink}" in out
    assert "definecolor{hsrtcite}" in out


def test_geometry_default_a4():
    out = HSRTReport(Section("Hi")).rendered
    assert "geometry" in out
    assert "top=2cm" in out


def test_custom_main_font():
    out = HSRTReport(Section("Hi"), main_font="Times").rendered
    assert "setmainfont{Times}" in out


def test_variant_default_inf():
    assert HSRTReport(Section("Hi")).variant is Variant.INF


def test_extra_packages_include_required():
    from pytex.packages import BIBLATEX, CLEVEREF, GLOSSARIES, HYPERREF
    doc = HSRTReport(Section("Hi"))
    pkgs = doc.packages
    for p in (HYPERREF, CLEVEREF, BIBLATEX, GLOSSARIES):
        assert p in pkgs
