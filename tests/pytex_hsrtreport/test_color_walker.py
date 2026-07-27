from pytex.commands.builtin import Section
from pytex.commands.colors import Textcolor
from pytex.model.color import Color
from pytex.model.concat import Concat
from pytex_hsrtreport import HSRTReport


def test_discovered_includes_hyperref_colors():
    doc = HSRTReport(Section("Hi"))
    names = {c.name for c in doc.discovered_colors()}
    assert {"hsrtcite", "hsrtlink", "hsrturl"} <= names


def test_discovered_includes_body_colors():
    body_color = Color.hex("#AABBCC", name="bodycol")
    doc = HSRTReport(Concat(Section("Hi"), Textcolor("bodycol", "x"), body_color))
    names = {c.name for c in doc.discovered_colors()}
    assert "bodycol" in names


def test_discovered_dedupes_by_name():
    a = Color.hex("#AABBCC", name="dupcol")
    b = Color.hex("#AABBCC", name="dupcol")
    doc = HSRTReport(Concat(a, b))
    names = [c.name for c in doc.discovered_colors() if c.name == "dupcol"]
    assert len(names) == 1


def test_rendered_emits_definecolor_for_body_color():
    Color.hex("#112233", name="custom1")
    doc = HSRTReport(Concat(Section("Hi"), Color.hex("#112233", name="custom2")))
    out = doc.rendered
    assert "definecolor{custom2}" in out
    assert "{HTML}{112233}" in out


def test_rendered_emits_hsrt_brand_definecolors():
    out = HSRTReport(Section("Hi")).rendered
    assert "definecolor{hsrtcite}" in out
    assert "definecolor{hsrtlink}" in out
    assert "definecolor{hsrturl}" in out


def test_user_preamble_color_collected():
    user = Color.hex("#DDEEFF", name="uppre")
    doc = HSRTReport(Section("Hi"), user_preamble=user)
    assert any(c.name == "uppre" for c in doc.discovered_colors())


def test_named_only_color_not_emitted():
    Color.named("red")
    out = HSRTReport(Concat(Section("Hi"), Color.named("red"))).rendered
    # xcolor already knows the base name `red`, so the preamble needs no
    # `\definecolor` line for it.
    assert "definecolor{red}" not in out
