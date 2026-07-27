from pytex.commands.font import Ttfamily, footnotesize, scriptsize
from pytex.interface.tex import TeX
from pytex_hsrtreport.listings import (
    HSRT_LISTING_BASE,
    HSRT_LISTING_STYLES,
    HSRTListingStyles,
    style_options,
)


def test_base_basicstyle_is_tex():
    val = HSRT_LISTING_BASE["basicstyle"]
    assert isinstance(val, TeX)


def test_base_basicstyle_renders_font_switches():
    val = HSRT_LISTING_BASE["basicstyle"]
    assert isinstance(val, TeX)
    assert "footnotesize" in val.rendered
    assert "ttfamily" in val.rendered


def test_styles_dict_has_expected_keys():
    for k in ("htmlCode", "phpCode", "jsCode", "shellCode", "shellCodeNOPASSWD", "URL"):
        assert k in HSRT_LISTING_STYLES


def test_html_style_basicstyle_is_scriptsize():
    val = HSRT_LISTING_STYLES["htmlCode"]["basicstyle"]
    assert isinstance(val, TeX)
    assert "scriptsize" in val.rendered


def test_html_style_keywordstyle_uses_color():
    val = HSRT_LISTING_STYLES["htmlCode"]["keywordstyle"]
    assert isinstance(val, TeX)
    assert "color{blue}" in val.rendered


def test_style_options_returns_copy():
    a = style_options("htmlCode")
    a["language"] = "modified"
    b = style_options("htmlCode")
    assert b["language"] == "html"


def test_rendered_emits_all_styles():
    out = HSRTListingStyles().rendered
    for name in HSRT_LISTING_STYLES:
        assert f"lstdefinestyle{{{name}}}" in out


def test_font_objects_render_zero_arg():
    # These font factories must render a bare switch. They must not wrap an
    # argument, because the listing styles concatenate the switches.
    assert footnotesize().rendered == r"\footnotesize"
    assert scriptsize().rendered == r"\scriptsize"
    assert Ttfamily().rendered == r"\ttfamily"
