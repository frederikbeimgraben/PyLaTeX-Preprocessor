from pytex.helpers.with_package import WithPackage
from pytex.model.concat import Concat
from pytex.model.control_sequence import ControlSequence, Parameter
from pytex.model.document import Document
from pytex.model.math import Align, Frac
from pytex.model.raw import Raw
from pytex.packages import AMSMATH
from pytex_tikz.tikz import Coordinate, Node, TikzPicture


def test_default_parent_none_for_detached():
    assert Raw("x").parent is None


def test_default_parents_empty_for_detached():
    assert Raw("x").parents == ()


def test_concat_sets_parent_on_children():
    a = Raw("a")
    b = Raw("b")
    c = Concat(a, b)
    assert a.parent is c
    assert b.parent is c


def test_concat_coerced_str_children_have_parent():
    c = Concat("hello", "world")
    coerced = c.elements[0]
    assert coerced.parent is c


def test_parameter_attaches_tex_value():
    inner = Raw("x")
    p = Parameter(inner)
    assert inner.parent is p


def test_control_sequence_attaches_params():
    p1 = Parameter("a")
    p2 = Parameter("b")
    cs = ControlSequence("frac", (p1, p2))
    assert p1.parent is cs
    assert p2.parent is cs


def test_with_package_attaches_child():
    inner = ControlSequence("foo", ())
    wp = WithPackage(inner, AMSMATH)
    assert inner.parent is wp


def test_document_attaches_body():
    body = Concat(Raw("x"))
    doc = Document(body)
    assert body.parent is doc


def test_parents_chain_through_tree():
    leaf = Raw("leaf")
    mid = Parameter(leaf)
    cs = ControlSequence("foo", (mid,))
    root = Concat(cs, Raw("tail"))
    assert leaf.parent is mid
    assert mid.parent is cs
    assert cs.parent is root
    assert leaf.parents == (mid, cs, root)


def test_nested_tex_through_math():
    frac = Frac("a", "b")
    align = Align(frac)
    inner_concat = align.child
    assert frac.parent is inner_concat
    assert inner_concat.parent is align
    assert frac.parents == (inner_concat, align)


def test_tikz_picture_attaches_elements():
    c = Coordinate("A", at=(0, 0))
    pic = TikzPicture(c)
    assert c.parent is pic


def test_tikz_node_attaches_tex_label():
    label = Raw("hi")
    n = Node(label=label)
    assert label.parent is n


def test_tikz_node_str_label_no_attach():
    n = Node(label="hi")
    assert n.parent is None
