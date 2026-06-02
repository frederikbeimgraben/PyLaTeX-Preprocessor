from pytex.model.concat import Concat
from pytex.model.document import Document
from pytex.model.raw import Raw
from pytex_hsrtreport import HSRTReport, InfoBox, WarningBox


def test_concat_three_levels_parents():
    leaf = Raw("leaf")
    mid = Concat(leaf, Raw("x"))
    root = Concat(mid, Raw("y"))
    assert leaf.parent is mid
    assert mid.parent is root
    assert leaf.parents == (mid, root)


def test_str_child_in_concat_gets_parent():
    c = Concat("hello", "world")
    assert c.elements[0].parent is c


def test_hsrtreport_attaches_body():
    body = Raw("text")
    doc = HSRTReport(body)
    assert body.parent is doc


def test_document_default_no_parent():
    assert Document("x").parent is None


def test_coloredbox_nested_parents_chain():
    inner = InfoBox("inner")
    outer = WarningBox(inner)
    assert inner.parent is outer
    assert outer in inner.parents


def test_coloredbox_parent_str_body_no_attach():
    box = InfoBox("plain string")
    # body is str; parent not assigned to str (skip)
    assert box.parent is None
