from pytex.model.concat import Concat
from pytex.model.empty import EmptyTeX
from pytex.model.raw import Raw


def test_empty():
    assert Concat().rendered == ""


def test_no_elements_collapses_to_empty():
    assert isinstance(Concat(), EmptyTeX)


def test_single_element_is_unwrapped():
    inner = Raw("solo")
    assert Concat(inner) is inner
    assert not isinstance(Concat("solo"), Concat)


def test_empty_children_are_stripped():
    c = Concat("a", "", Raw(""), "b")
    assert [ch.rendered for ch in c.children] == ["a", "b"]


def test_stripping_does_not_change_rendering():
    # An empty child renders to nothing, so `Concat` can drop it and still
    # render the same string.
    assert Concat("a", Raw(""), "", "b").rendered == "ab"


def test_whitespace_children_are_kept():
    # A single space carries meaning, for example between `\item` and its body.
    assert Concat("a", " ", "b").rendered == "a b"


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
    assert len(children) == 3  # `coerce_tex` makes a `Raw` node from each `str`.
    assert all(hasattr(ch, "rendered") for ch in children)


def test_str_dunder():
    assert str(Concat("a", "b")) == "ab"


def test_nested():
    inner = Concat("a", "b")
    outer = Concat("[", inner, "]")
    assert outer.rendered == "[ab]"
