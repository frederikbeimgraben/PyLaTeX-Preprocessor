from pytex.model.concat import Concat
from pytex.model.raw import Raw


def test_empty():
    assert Concat().rendered == ""


def test_string_only():
    assert Concat("a", "b", "c").rendered == "abc"


def test_mixed_str_and_tex():
    assert Concat("x ", Raw("y"), " z").rendered == "x y z"


def test_render_idempotent():
    c = Concat("a", "b")
    assert c.rendered == c.rendered == "ab"


def test_children_only_tex():
    c = Concat("a", Raw("b"), "c")
    children = c.children
    assert len(children) == 3  # str coerced to Raw via coerce_tex
    assert all(hasattr(ch, "rendered") for ch in children)


def test_str_dunder():
    assert str(Concat("a", "b")) == "ab"


def test_nested():
    inner = Concat("a", "b")
    outer = Concat("[", inner, "]")
    assert outer.rendered == "[ab]"
