from pytex.packages import FONTAWESOME, MDFRAMED, XCOLOR
from pytex_hsrtreport.boxes import (
    ColoredBox,
    CustomBox,
    DiscussionBox,
    ImportantBox,
    InfoBox,
    SuccessBox,
    WarningBox,
)


def test_info_box_returns_colored_box():
    b = InfoBox("hi")
    assert isinstance(b, ColoredBox)
    assert b.background_color == "blue"


def test_top_level_nesting_is_one():
    assert InfoBox("x").nesting_level == 1


def test_nesting_two_levels():
    inner = InfoBox("inner")
    _ = WarningBox(inner)
    assert inner.nesting_level == 2


def test_nesting_three_levels():
    inner = InfoBox("inner")
    _ = SuccessBox(WarningBox(inner))
    assert inner.nesting_level == 3


def test_opacity_formula_level_1():
    b = InfoBox("x")
    assert b.background_opacity == round((0.05 + 0.075 * 1) * 100)
    assert b.icon_opacity == b.background_opacity + 20


def test_opacity_formula_level_3():
    inner = InfoBox("inner")
    _ = WarningBox(SuccessBox(inner))
    expected_bg = round((0.05 + 0.075 * 3) * 100)
    assert inner.background_opacity == expected_bg
    assert inner.icon_opacity == expected_bg + 20


def test_renders_with_computed_opacities():
    inner = InfoBox("inner")
    _ = WarningBox(inner)
    out = inner.rendered
    bg = round((0.05 + 0.075 * 2) * 100)
    assert f"backgroundcolor=blue!{bg}" in out


def test_requires_packages():
    req = InfoBox("x").requires
    assert MDFRAMED in req and XCOLOR in req and FONTAWESOME in req


def test_preset_colors():
    assert WarningBox("x").background_color == "red"
    assert SuccessBox("x").background_color == "green"
    assert ImportantBox("x").background_color == "orange"
    assert DiscussionBox("x").background_color == "hanblue"


def test_custom_box_accepts_color():
    b = CustomBox("body", "thumbs-up", "navyblue")
    assert b.background_color == "navyblue"


def test_top_level_renders_no_parent():
    b = InfoBox("hello")
    out = b.rendered
    assert "mdframed" in out and "hello" in out
