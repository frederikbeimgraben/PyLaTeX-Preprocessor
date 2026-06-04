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
    out_off = HSRTReport(
        Section("Hi"), show_glossary=False, show_acronyms=False
    ).rendered
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


def test_center_footer_shows_on_all_pages_including_backmatter():
    """The "Seite X von Y" centre footer must render on every numbered page.

    Regression: it used to be wrapped in ``\\ifHSRTBackMatter\\else ... \\fi``,
    so it vanished on back-matter pages (e.g. the bibliography, which is the
    document's last page). The footer content must not be gated by
    ``\\ifHSRTBackMatter``.
    """
    out = HSRTReport(Section("Hi")).rendered
    assert r"\cfoot{Seite~\thepage\ifHSRTNumberedBody~von~\pageref{LastPage}\fi}" in out
    # The centre footer must NOT be suppressed in back matter.
    assert r"\cfoot{\ifHSRTBackMatter" not in out


def test_lastpage_suffix_uses_numbered_body_flag():
    """ "von \\pageref{LastPage}" must survive \\backmatter.

    ``\\backmatter`` sets ``\\@mainmatterfalse``, so gating the suffix on
    ``\\if@mainmatter`` dropped it on back-matter pages. ``\\ifHSRTNumberedBody``
    is set at ``\\mainmatter`` and never reset, so it stays true through back
    matter while remaining false in (roman) front matter.
    """
    out = HSRTReport(Section("Hi")).rendered
    assert r"\newif\ifHSRTNumberedBody" in out
    # The redefined \mainmatter turns the flag on.
    assert r"\HSRTNumberedBodytrue" in out
    # The suffix is gated on the new flag, not on \if@mainmatter.
    assert r"\ifHSRTNumberedBody~von~\pageref{LastPage}" in out
    assert r"\if@mainmatter~von~\pageref{LastPage}" not in out


def test_extra_packages_include_required():
    from pytex.packages import BIBLATEX, CLEVEREF, GLOSSARIES, HYPERREF

    doc = HSRTReport(Section("Hi"))
    pkgs = doc.packages
    for p in (HYPERREF, CLEVEREF, BIBLATEX, GLOSSARIES):
        assert p in pkgs
