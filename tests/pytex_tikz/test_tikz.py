import pytest

from pytex.model.document import Document
from pytex.packages import PGF, TIKZ
from pytex_tikz.tikz import (
    Circle,
    Coordinate,
    Draw,
    Fill,
    Node,
    Rectangle,
    Scope,
    TikzLibrary,
    TikzPicture,
)


def test_coordinate_named_only():
    assert Coordinate("A").rendered == r"\coordinate (A);"


def test_coordinate_with_position():
    assert Coordinate("A", at=(1, 2)).rendered == r"\coordinate (A) at (1,2);"


def test_coordinate_requires_tikz():
    assert TIKZ in Coordinate("A").requires


def test_node_basic():
    out = Node(label="hello").rendered
    assert "{hello}" in out
    assert out.startswith(r"\node") and out.endswith(";")


def test_node_with_name_and_position():
    out = Node(label="x", name="n1", at=(0, 0)).rendered
    assert "(n1)" in out and "(0,0)" in out and "{x}" in out


def test_node_with_options():
    out = Node(label="x", options=("draw", ("color", "red"))).rendered
    assert "draw" in out and "color=red" in out


def test_node_requires_tikz():
    assert TIKZ in Node(label="x").requires


def test_node_children_when_tex_label():
    from pytex.model.raw import Raw

    label = Raw("inner")
    n = Node(label=label)
    assert n.children == (label,)


def test_node_children_when_str_label():
    assert Node(label="hi").children == ()


def test_draw_two_points():
    out = Draw(((0, 0), (1, 1))).rendered
    assert out == r"\draw (0,0) -- (1,1);"


def test_draw_with_options_and_cycle():
    out = Draw(((0, 0), (1, 0), (1, 1)), options=("thick",), cycle=True).rendered
    assert "[thick]" in out
    assert "cycle" in out


def test_draw_uses_named_coordinate():
    c = Coordinate("A", at=(0, 0))
    out = Draw((c, (1, 1))).rendered
    assert "(A) -- (1,1)" in out


def test_draw_uses_named_node():
    n = Node(label="x", name="n1")
    out = Draw(((0, 0), n)).rendered
    assert "(n1)" in out


def test_node_without_name_as_position_raises():
    n = Node(label="x")
    with pytest.raises(ValueError):
        _ = Draw(((0, 0), n)).rendered


def test_fill():
    out = Fill(((0, 0), (1, 0), (1, 1))).rendered
    assert out.startswith(r"\fill")
    assert "cycle" in out


def test_circle_basic():
    out = Circle((0, 0), 1).rendered
    assert out == r"\draw (0,0) circle (1);"


def test_circle_fill():
    out = Circle((0, 0), 1, fill=True).rendered
    assert out.startswith(r"\fill")


def test_rectangle():
    out = Rectangle((0, 0), (2, 1)).rendered
    assert out == r"\draw (0,0) rectangle (2,1);"


def test_rectangle_fill():
    out = Rectangle((0, 0), (1, 1), fill=True).rendered
    assert out.startswith(r"\fill")


def test_tikz_picture_renders_env():
    p = TikzPicture(Coordinate("A", at=(0, 0)))
    out = p.rendered
    assert out.startswith(r"\begin{tikzpicture}")
    assert out.endswith(r"\end{tikzpicture}")


def test_tikz_picture_requires_tikz_and_pgf():
    p = TikzPicture(Coordinate("A"))
    assert TIKZ in p.requires
    assert PGF in p.requires


def test_tikz_picture_options():
    out = TikzPicture(Coordinate("A"), options=(("scale", "2"),)).rendered
    assert "[scale=2]" in out


def test_tikz_library():
    out = TikzLibrary("arrows.meta").rendered
    assert out == r"\usetikzlibrary{arrows.meta}"


def test_scope_renders():
    s = Scope(Coordinate("A"), options=("dashed",))
    out = s.rendered
    assert out.startswith(r"\begin{scope}[dashed]")
    assert out.endswith(r"\end{scope}")


def test_tikz_packages_in_document():
    pic = TikzPicture(Coordinate("A", at=(0, 0)))
    out = Document(pic).rendered
    assert r"\usepackage{tikz}" in out
    assert r"\usepackage{pgf}" in out
