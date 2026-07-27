from pytex.commands.colors import Textcolor
from pytex.model.color import Color
from pytex.model.concat import Concat
from pytex_hsrtreport import HSRTReport
from pytex_hsrtreport.titlepage import TitlePageDataLine


def test_discovered_colors_includes_data_line_color():
    color = Color.hex("FF8800", name="dataline_col")
    value = Concat(color, Textcolor(color.name, "Prof. X"))
    doc = HSRTReport(
        body="text",
        title="T",
        data_lines=(TitlePageDataLine("Betreuer", value),),
    )
    names = {c.name for c in doc.discovered_colors()}
    assert color.name in names


def test_rendered_defines_color_used_only_in_data_line():
    color = Color.hex("FF8800", name="dataline_only")
    value = Concat(color, Textcolor(color.name, "Prof. X"))
    doc = HSRTReport(
        body="text",
        title="T",
        data_lines=(TitlePageDataLine("Betreuer", value),),
    )
    out = doc.rendered
    assert "\\textcolor{dataline_only}" in out
    assert "definecolor{dataline_only}" in out


def test_rendered_defines_color_used_only_in_abstract():
    color = Color.hex("00AACC", name="abstract_only")
    doc = HSRTReport(
        body="text",
        title="T",
        abstract=Concat(Textcolor(color.name, "important"), color),
    )
    out = doc.rendered
    assert "definecolor{abstract_only}" in out
