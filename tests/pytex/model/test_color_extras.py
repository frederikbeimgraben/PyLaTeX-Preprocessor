from pytex.commands.colors import Definecolor, SelectColor, Textcolor
from pytex.model.color import Color, ColorSpec, collect_colors
from pytex.model.concat import Concat


def test_colorspec_equality():
    assert ColorSpec("HTML", "FF0000") == ColorSpec("HTML", "FF0000")
    assert ColorSpec("HTML", "FF0000") != ColorSpec("rgb", "1,0,0")


def test_colorspec_hash_equal_when_eq():
    a = ColorSpec("HTML", "FF0000")
    b = ColorSpec("HTML", "FF0000")
    assert hash(a) == hash(b)


def test_color_equality_via_name_and_spec():
    a = Color.hex("#FF0000")
    b = Color.hex("#FF0000")
    assert a == b
    assert hash(a) == hash(b)


def test_color_inequality():
    assert Color.hex("#FF0000") != Color.hex("#00FF00")


def test_color_repr_contains_name():
    c = Color.hex("#FF0000")
    assert "cFF0000" in repr(c)


def test_overload_three_floats_tuple():
    c = Color((0.1, 0.2, 0.3))
    assert c.spec is not None
    assert c.spec.model == "rgb"


def test_overload_three_ints_tuple():
    c = Color((1, 2, 3))
    assert c.spec is not None
    assert c.spec.model == "RGB"


def test_overload_unknown_named_raises():
    import pytest

    with pytest.raises(ValueError):
        Color("not_a_known_name")


def test_color_requires_xcolor():
    from pytex.packages import XCOLOR

    assert XCOLOR in Color.named("red").requires


def test_tint_chain():
    import pytest

    # blue!50!80 is not a name xcolor can resolve: it reads the token after
    # the second "!" as a color name, not as a second tint percentage.
    with pytest.raises(ValueError):
        Color.named("blue").tint(50).tint(80)


def test_or_alias_returns_color():
    c = Color.named("red") | Color.named("blue")
    assert isinstance(c, Color)


def test_collect_colors_unique_by_name():
    c = Color.hex("#FF0000")
    same = Color.hex("#FF0000")
    out = collect_colors(Concat(c, same))
    assert len(out) == 1


def test_collect_colors_distinguishes_close_rgb_defaults():
    # Two close but different rgb() colors must not share a default name.
    # A shared name means one \definecolor line silently wins for both.
    a = Color.rgb(0.5, 0.2, 0.1)
    b = Color.rgb(0.501, 0.2, 0.1)
    assert a.name != b.name
    out = collect_colors(Concat(a, b))
    assert len(out) == 2


def test_collect_colors_returns_empty_for_pure_named():
    tree = Concat(Color.named("red"), Color.named("blue"))
    assert collect_colors(tree) == ()


def test_collect_colors_nested_deep():
    leaf = Color.hex("#ABCDEF")
    tree = Concat("a", Concat("b", Concat(leaf)))
    assert collect_colors(tree)[0].name == "cABCDEF"


def test_selectcolor_renders():
    assert SelectColor("red").rendered == r"\color{red}"


def test_textcolor_renders():
    assert Textcolor("red", "x").rendered == r"\textcolor{red}{x}"


def test_definecolor_with_color_instance():
    c = Color.hex("#FF8800")
    assert c.spec is not None
    out = Definecolor(c.name, c.spec.model, c.spec.value).rendered
    assert "FF8800" in out and "{HTML}" in out


def test_color_named_does_not_register_arbitrary():
    import pytest

    with pytest.raises(ValueError):
        Color.named("magenta_extra")


def test_register_then_named_works():
    from pytex.model.color import register_named_color

    register_named_color("hsrtgreen")
    Color.named("hsrtgreen")  # This call must not raise.


def test_named_blue_no_spec():
    assert Color.named("blue").spec is None
