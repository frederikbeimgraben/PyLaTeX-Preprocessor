import pytest

from pytex.model.color import (
    Color,
    ColorSpec,
    collect_colors,
    is_known_color_name,
    register_named_color,
)
from pytex.model.concat import Concat


def test_hex_constructor():
    c = Color.hex("#FF0000")
    assert c.name == "cFF0000"
    assert c.spec == ColorSpec("HTML", "FF0000")


def test_hex_invalid():
    with pytest.raises(ValueError):
        Color.hex("zzz")


def test_rgb255_constructor():
    c = Color.rgb255(255, 0, 128, name="mypink")
    assert c.name == "mypink"
    assert c.spec == ColorSpec("RGB", "255,0,128")


def test_rgb255_out_of_range():
    with pytest.raises(ValueError):
        Color.rgb255(300, 0, 0)


def test_rgb_constructor():
    c = Color.rgb(0.5, 0.5, 0.5, name="g50")
    assert c.spec == ColorSpec("rgb", "0.5,0.5,0.5")


def test_rgb_out_of_range():
    with pytest.raises(ValueError):
        Color.rgb(2.0, 0.0, 0.0)


def test_named_constructor():
    assert Color.named("blue").name == "blue"
    assert Color.named("blue").spec is None


def test_named_unknown_raises():
    with pytest.raises(ValueError):
        Color.named("definitely_not_a_color")


def test_overload_hex():
    c = Color("#00FF00")
    assert c.spec == ColorSpec("HTML", "00FF00")


def test_overload_name():
    c = Color("red")
    assert c.spec is None
    assert c.name == "red"


def test_overload_rgb255_tuple():
    c = Color((10, 20, 30))
    assert c.spec == ColorSpec("RGB", "10,20,30")


def test_overload_rgb_tuple():
    c = Color((0.1, 0.2, 0.3))
    assert c.spec == ColorSpec("rgb", "0.1,0.2,0.3")


def test_overload_unknown_type():
    with pytest.raises(TypeError):
        Color(123)  # type: ignore[arg-type]


def test_tint():
    c = Color.named("blue").tint(50)
    assert c.name == "blue!50"
    assert c.spec is None


def test_mix():
    c = Color.named("red").mix(Color.named("blue"), 30)
    assert c.name == "red!30!blue"


def test_or_operator_aliases_mix():
    c = Color.named("red") | Color.named("blue")
    assert "red!50!blue" == c.name


def test_register_named_color():
    register_named_color("hsrtgray")
    assert is_known_color_name("hsrtgray")
    Color.named("hsrtgray")  # no raise


def test_rendered_is_name():
    assert Color.hex("#FF0000").rendered == "cFF0000"


def test_collect_colors_walks_tree():
    c1 = Color.hex("#AA0000")
    c2 = Color.hex("#00BB00")
    tree = Concat("a", c1, "b", Concat(c2))
    colors = collect_colors(tree)
    names = {c.name for c in colors}
    assert "cAA0000" in names and "c00BB00" in names


def test_collect_colors_skips_named_without_spec():
    tree = Concat(Color.named("red"))
    assert collect_colors(tree) == ()
