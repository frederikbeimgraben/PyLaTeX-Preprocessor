import pytest

from pytex.model.image import IncludeImage
from pytex_hsrtreport import Variant
from pytex_hsrtreport.logos import (
    DefaultLogos,
    Logo,
    LogoStrip,
    logo_path,
)


def test_logo_returns_include_image():
    assert isinstance(Logo("HSRT", inline_base64=False), IncludeImage)


def test_logo_default_inline_true():
    img = Logo("INF")
    assert isinstance(img, IncludeImage)
    assert img.inline_base64 is True


def test_logo_path_resolves_to_assets():
    p = logo_path("HSRT")
    assert p.name == "HSRT.pdf"
    assert p.exists()


def test_logo_path_unknown_raises():
    with pytest.raises(ValueError):
        logo_path("NOPE")


def test_logo_path_accepts_custom_file(tmp_path):
    custom = tmp_path / "mylogo.png"
    custom.write_bytes(b"\x89PNG")
    assert logo_path(str(custom)) == custom


def test_logo_output_name_disambiguates_custom_paths(tmp_path):
    from pytex_hsrtreport.logos import logo_output_name

    a = tmp_path / "a" / "logo.png"
    b = tmp_path / "b" / "logo.png"
    for p in (a, b):
        p.parent.mkdir(parents=True)
        p.write_bytes(b"\x89PNG")
    # Two custom logos share the stem `logo` but sit in different directories.
    # Their output names must differ, or they collide in `logos/`.
    assert logo_output_name(str(a)) != logo_output_name(str(b))
    # A vendored name keeps its clean stem.
    assert logo_output_name("INF") == "INF.pdf"


def test_logo_rendering_includes_resolved_path():
    out = Logo("HSRT", inline_base64=False, scale=0.5).rendered
    assert "HSRT.pdf" in out
    assert "scale=0.5" in out


def test_logo_height_overrides_scale():
    img = Logo("HSRT", inline_base64=False, height="2cm")
    out = img.rendered
    assert "height=2cm" in out
    assert "scale=" not in out


def test_logo_strip_separators():
    out = LogoStrip(("HSRT", "INF"), inline_base64=False).rendered
    parts = out.split("\\hspace{0.5cm}")
    assert len(parts) == 2


def test_logo_strip_empty_renders_empty():
    assert LogoStrip((), inline_base64=False).rendered == ""


def test_default_logos_for_inf():
    out = DefaultLogos(Variant.INF, inline_base64=False).rendered
    assert "INF.pdf" in out


def test_default_logos_for_stupa():
    out = DefaultLogos(Variant.STUPA, inline_base64=False).rendered
    assert "STUPA.pdf" in out


def test_makers_logo_path_resolves_to_vendored_svg():
    p = logo_path("MAKERS")
    assert p.name == "MAKERS.svg"
    assert p.exists()


def test_makers_ralign_logo_path_resolves_to_vendored_svg():
    p = logo_path("MAKERS-RAlign")
    assert p.name == "MAKERS-RAlign.svg"
    assert p.exists()


def test_default_logos_for_makers():
    # PyTeX converts an SVG logo to PDF. So the rendered `.tex` file names the
    # converted `.pdf` file, not the `.svg` source.
    out = DefaultLogos(Variant.MAKERS, inline_base64=False).rendered
    assert "MAKERS" in out and ".pdf" in out


def test_makers_footer_logo_differs_from_title():
    from pytex_hsrtreport.variants import default_logo_names, footer_logo_names

    # The title page uses the left-aligned logo. The footer uses the
    # right-aligned logo.
    assert default_logo_names(Variant.MAKERS) == ("MAKERS",)
    assert footer_logo_names(Variant.MAKERS) == ("MAKERS-RAlign",)


def test_footer_logos_default_to_title_logos():
    from pytex_hsrtreport.variants import default_logo_names, footer_logo_names

    # A variant with no footer override uses its title-page logos again.
    for variant in (Variant.INF, Variant.STUPA, Variant.ASTA, Variant.ECHO):
        assert footer_logo_names(variant) == default_logo_names(variant)


def test_inline_logo_collected_by_document():
    from pytex_hsrtreport import HSRTReport

    body = Logo("HSRT", inline_base64=True)
    doc = HSRTReport(body)
    images = doc.inline_images
    assert len(images) == 1
    assert images[0].resolved_path.name == "HSRT.pdf"


def test_inline_logo_appears_in_rendered():
    from pytex_hsrtreport import HSRTReport

    out = HSRTReport(Logo("HSRT", inline_base64=True)).rendered
    assert "filecontents*" in out
    assert "HSRT.pdf.b64" in out
