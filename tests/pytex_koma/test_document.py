import pytest

from pytex_koma import KOMA_CLASSES, KomaDocument


def test_koma_classes_set():
    assert frozenset({"scrartcl", "scrreprt", "scrbook", "scrlttr2"}) == KOMA_CLASSES


def test_default_class_valid():
    doc = KomaDocument("body")
    assert doc.document_class == "scrartcl"


@pytest.mark.parametrize("cls", sorted(KOMA_CLASSES))
def test_accepts_each_koma_class(cls):
    doc = KomaDocument("x", document_class=cls)
    assert f"\\documentclass{{{cls}}}" in doc.rendered or f"]{{{cls}}}" in doc.rendered


@pytest.mark.parametrize("bad", ["article", "report", "book", "letter", ""])
def test_rejects_non_koma_class(bad):
    with pytest.raises(ValueError):
        KomaDocument("x", document_class=bad)


def test_paper_flag():
    doc = KomaDocument("x", paper="a4paper")
    assert "a4paper" in doc.rendered


def test_paper_keyvalue():
    doc = KomaDocument("x", paper="a3")
    assert "paper=a3" in doc.rendered


def test_fontsize_flag():
    doc = KomaDocument("x", fontsize="11pt")
    assert "11pt" in doc.rendered
    assert "fontsize=11pt" not in doc.rendered


def test_fontsize_keyvalue():
    doc = KomaDocument("x", fontsize="14pt")
    assert "fontsize=14pt" in doc.rendered


def test_bcor():
    doc = KomaDocument("x", bcor="10mm")
    assert "BCOR=10mm" in doc.rendered


def test_div_int():
    doc = KomaDocument("x", div=12)
    assert "DIV=12" in doc.rendered


def test_div_str():
    doc = KomaDocument("x", div="calc")
    assert "DIV=calc" in doc.rendered


def test_two_side_true():
    assert "twoside" in KomaDocument("x", two_side=True).rendered


def test_two_side_false():
    assert "oneside" in KomaDocument("x", two_side=False).rendered


def test_landscape():
    assert "landscape" in KomaDocument("x", landscape=True).rendered


def test_title_page_false():
    assert "notitlepage" in KomaDocument("x", title_page=False).rendered


def test_draft_false_is_final():
    assert "final" in KomaDocument("x", draft=False).rendered


def test_draft_true():
    assert "draft" in KomaDocument("x", draft=True).rendered


def test_open_at():
    doc = KomaDocument("x", document_class="scrbook", open_at="right")
    assert "open=right" in doc.rendered


def test_chapter_prefix_true():
    doc = KomaDocument("x", document_class="scrbook", chapter_prefix=True)
    assert "chapterprefix=true" in doc.rendered


def test_headings():
    assert "headings=big" in KomaDocument("x", headings="big").rendered


def test_parskip():
    assert "parskip=half" in KomaDocument("x", parskip="half").rendered


def test_bibliography():
    assert "bibliography=totoc" in KomaDocument("x", bibliography="totoc").rendered


def test_extra_class_options_merged():
    doc = KomaDocument("x", extra_class_options={"someflag"})
    assert "someflag" in doc.rendered


def test_native_and_explicit_options_merge():
    doc = KomaDocument(
        "x",
        paper="a4paper",
        document_class_options={"twocolumn"},
    )
    out = doc.rendered
    assert "a4paper" in out and "twocolumn" in out
