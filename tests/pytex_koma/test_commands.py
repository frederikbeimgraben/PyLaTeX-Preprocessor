from pytex.helpers.with_package import WithPackage
from pytex.packages import SCRLAYER_SCRPAGE, TYPEAREA
from pytex_koma import (
    Addchap,
    Addsec,
    Addtokomafont,
    Appendix,
    Areaset,
    Automark,
    Backmatter,
    Cfoot,
    Chead,
    Clearpairofpagestyles,
    Dictum,
    Frontmatter,
    Ifoot,
    Ihead,
    KOMAoption,
    KOMAoptions,
    Mainmatter,
    Minisec,
    Ofoot,
    Ohead,
    Pagestyle,
    Setkomafont,
    Subject,
    Subtitle,
    Typearea,
)


def test_addsec():
    assert Addsec("Intro").rendered == r"\addsec{Intro}"


def test_addsec_short():
    assert Addsec("Long", short="Short").rendered == r"\addsec[Short]{Long}"


def test_addchap():
    assert Addchap("Ch").rendered == r"\addchap{Ch}"


def test_minisec():
    assert Minisec("x").rendered == r"\minisec{x}"


def test_frontmatter_mainmatter_backmatter_appendix():
    assert Frontmatter().rendered == r"\frontmatter"
    assert Mainmatter().rendered == r"\mainmatter"
    assert Backmatter().rendered == r"\backmatter"
    assert Appendix().rendered == r"\appendix"


def test_subtitle():
    assert Subtitle("s").rendered == r"\subtitle{s}"


def test_subject():
    assert Subject("s").rendered == r"\subject{s}"


def test_dictum_no_author():
    assert Dictum("text").rendered == r"\dictum{text}"


def test_dictum_with_author():
    assert Dictum("text", author="Spock").rendered == r"\dictum[Spock]{text}"


def test_komaoptions_dict():
    out = KOMAoptions({"paper": "a4", "fontsize": "12pt"}).rendered
    assert out.startswith(r"\KOMAoptions{") and out.endswith("}")
    assert "paper=a4" in out and "fontsize=12pt" in out


def test_komaoption():
    assert KOMAoption("paper", "a4").rendered == r"\KOMAoption{paper}{a4}"


def test_setkomafont():
    assert (
        Setkomafont("disposition", r"\rmfamily").rendered
        == r"\setkomafont{disposition}{\rmfamily}"
    )


def test_addtokomafont():
    assert (
        Addtokomafont("section", r"\bfseries").rendered
        == r"\addtokomafont{section}{\bfseries}"
    )


def test_areaset_basic():
    a = Areaset("12cm", "20cm")
    assert isinstance(a, WithPackage)
    assert TYPEAREA in a.requires
    assert a.rendered == r"\areaset{12cm}{20cm}"


def test_areaset_with_bcor():
    out = Areaset("12cm", "20cm", bcor="5mm").rendered
    assert out == r"\areaset[5mm]{12cm}{20cm}"


def test_typearea_requires_pkg():
    t = Typearea(11)
    assert TYPEAREA in t.requires


def test_pagestyle_requires_scrlayer():
    p = Pagestyle("scrheadings")
    assert SCRLAYER_SCRPAGE in p.requires


def test_clearpairofpagestyles():
    c = Clearpairofpagestyles()
    assert SCRLAYER_SCRPAGE in c.requires


def test_head_foot_commands_attach_pkg():
    for fn in (Ihead, Chead, Ohead, Ifoot, Cfoot, Ofoot):
        out = fn("x")
        assert SCRLAYER_SCRPAGE in out.requires


def test_ihead_with_scope():
    out = Ihead("text", scope="L").rendered
    assert out == r"\ihead[L]{text}"


def test_automark_one_arg():
    a = Automark("section")
    assert SCRLAYER_SCRPAGE in a.requires
    assert a.rendered == r"\automark{section}"


def test_automark_two_args():
    out = Automark("section", second="subsection").rendered
    assert out == r"\automark[subsection]{section}"
