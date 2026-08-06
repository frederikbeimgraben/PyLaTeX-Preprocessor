"""Tests for the `footer_logos` override of `HSRTReport`.

The title-page logos and the footer logos are two separate sets. `logos`
overrides the first set and `footer_logos` the second. `None` keeps the set
that the variant defines.

Every variant these tests use has PDF logos, so no test needs inkscape.
"""

from pytex.commands.builtin import Section
from pytex_hsrtreport import HSRTReport, Variant


def _report(
    variant: Variant,
    *,
    logos: tuple[str, ...] | None = None,
    footer_logos: tuple[str, ...] | None = None,
    title: str | None = None,
) -> HSRTReport:
    return HSRTReport(
        Section("Hi"),
        variant=variant,
        show_footer_logos=True,
        logos=logos,
        footer_logos=footer_logos,
        title=title,
    )


def test_footer_logos_default_to_the_variant_set():
    report = _report(Variant.MAKERS)
    assert report.footer_logos is None
    # The MAKERS variant puts the right-aligned logo in the footer.
    assert "logos/MAKERS-RAlign.pdf" in report.rendered


def test_explicit_footer_logos_win_over_the_variant_set():
    out = _report(Variant.STUPA, footer_logos=("INF",)).rendered
    assert "logos/INF.pdf" in out
    # No title page renders without a title, so the STUPA logo of the variant
    # can only come from the footer hook. Its absence proves the override.
    assert "logos/STUPA.pdf" not in out


def test_footer_logos_are_independent_of_the_title_logos():
    report = _report(
        Variant.STUPA,
        title="T",
        logos=("HSRT",),
        footer_logos=("INF",),
    )
    out = report.rendered
    assert "logos/HSRT.pdf" in out
    assert "logos/INF.pdf" in out
    assert "logos/STUPA.pdf" not in out


def test_footer_logos_stay_off_when_the_footer_is_off():
    out = HSRTReport(
        Section("Hi"), variant=Variant.STUPA, footer_logos=("INF",)
    ).rendered
    assert "logos/INF.pdf" not in out


def test_write_inline_logos_emits_the_overridden_footer_set(tmp_path):
    report = _report(Variant.STUPA, footer_logos=("INF",))
    report.write_inline_logos(str(tmp_path))
    written = {p.name for p in (tmp_path / "logos").iterdir()}
    # The title set, the overridden footer set and the skyline all land on
    # disk. The tikz overlays name each of them.
    assert written == {"STUPA.pdf", "INF.pdf", "Skyline.pdf"}


def test_write_inline_logos_keeps_the_variant_set_without_an_override(tmp_path):
    report = _report(Variant.STUPA)
    report.write_inline_logos(str(tmp_path))
    written = {p.name for p in (tmp_path / "logos").iterdir()}
    assert written == {"STUPA.pdf", "Skyline.pdf"}
