"""Tests for Markdown output variants (--variant / --config)."""

import pytest

from pytex.model.document import Document
from pytex_builder.variants import VARIANT_NAMES, build_document
from pytex_hsrtreport.document import HSRTReport
from pytex_hsrtreport.variants import Variant


def test_plain_is_a_document_with_default_class():
    doc = build_document("Just text.", variant="plain")
    assert isinstance(doc, Document)
    assert doc.document_class == "article"


def test_plain_config_sets_class_and_options():
    doc = build_document(
        "x",
        variant="plain",
        config={"documentclass": "scrartcl", "classoptions": ["11pt", "twocolumn"]},
    )
    assert doc.document_class == "scrartcl"
    assert {str(o) for o in doc.document_class_options} == {"11pt", "twocolumn"}


def test_config_key_value_option_becomes_pair():
    doc = build_document("x", variant="plain", config={"classoptions": ["DIV=12"]})
    assert ("DIV", "12") in doc.document_class_options


def test_report_derives_title_from_first_heading():
    report = build_document("# Derived Title\n\nbody", variant="report")
    assert isinstance(report, HSRTReport)
    assert report.title == "Derived Title"
    assert report.show_titlepage is True
    # The heading also stays in the body as a big, unnumbered chapter (not a
    # numbered \chapter, which would duplicate the title-page heading number).
    assert r"\chapter*{Derived Title}" in report.rendered
    assert r"\chapter{Derived Title}" not in report.rendered


def test_report_derived_title_unnumbered_heading_only_when_derived():
    # A frontmatter title is not pulled from the body, so no \chapter* is added.
    out = build_document("---\ntitle: T\n---\n# Top\n\nbody", variant="report").rendered
    assert r"\chapter*{" not in out


def test_report_explicit_title_wins_over_heading():
    report = build_document(
        "# Heading\n\nbody", variant="report", config={"title": "Explicit"}
    )
    assert report.title == "Explicit"


def test_report_top_headings_become_chapters_not_0x_sections():
    # `#` is consumed as the title, so the body's top level is `##`; those must
    # still render as chapters (not chapterless 0.x sections).
    out = build_document(
        "# Title\n\n## One\n\ntext\n\n## Two\n\nmore", variant="report"
    ).rendered
    assert r"\chapter{One}" in out and r"\chapter{Two}" in out


def test_report_with_frontmatter_title_keeps_hash_as_chapter():
    out = build_document(
        "---\ntitle: T\n---\n# Top\n\n## Sub", variant="report"
    ).rendered
    assert r"\chapter{Top}" in out
    assert r"\section{Sub}" in out


def test_report_without_heading_has_no_titlepage():
    report = build_document("plain paragraph only", variant="report")
    assert report.show_titlepage is False


def test_report_title_is_latex_escaped():
    report = build_document("# A & B", variant="report")
    assert report.title == r"A \& B"


def test_protocol_asta_forces_asta_variant():
    report = build_document(
        "---\ngremium: StuPa\n---\n# TOP 1\n\nx", variant="protocol-asta"
    )
    assert isinstance(report, HSRTReport)
    assert report.variant is Variant.ASTA


def test_protocol_stupa_forces_stupa_variant():
    report = build_document("# TOP 1\n\nx", variant="protocol-stupa")
    assert report.variant is Variant.STUPA


def test_auto_detects_protocol_from_gremium():
    report = build_document("---\ngremium: AStA\n---\n# TOP\n\nx")
    assert isinstance(report, HSRTReport)
    assert report.variant is Variant.ASTA


def test_auto_defaults_to_plain():
    assert isinstance(build_document("# H\n\ntext"), Document)


def test_unknown_variant_raises():
    with pytest.raises(ValueError, match="unknown variant"):
        build_document("x", variant="nope")


def test_variant_names_are_the_public_styles():
    assert VARIANT_NAMES == ("plain", "report", "protocol-asta", "protocol-stupa")


def test_report_data_lines_from_frontmatter():
    src = (
        "---\ntitle: T\ndatalines:\n"
        "  - 'Version: 1.0'\n  - 'Date: 2026-06-02'\n---\n## X"
    )
    out = build_document(src, variant="report").rendered
    assert "Version" in out and "1.0" in out
    assert "Date" in out and "2026-06-02" in out


def test_report_data_lines_skip_entries_without_colon():
    report = build_document(
        "---\ntitle: T\ndatalines:\n  - 'no colon here'\n  - 'Key: val'\n---\n## X",
        variant="report",
    )
    assert isinstance(report, HSRTReport)
    assert [line.label for line in report.data_lines] == ["Key"]


def test_report_abstract_and_keywords_from_frontmatter():
    out = build_document(
        "---\ntitle: T\nabstract: My summary\nkeywords: [a, b, c]\n---\n## X",
        variant="report",
    ).rendered
    assert "My summary" in out
    assert "a, b, c" in out


def test_report_data_lines_latex_escaped():
    report = build_document(
        "---\ntitle: T\ndatalines:\n  - 'A & B: x_y'\n---\n## X", variant="report"
    )
    assert isinstance(report, HSRTReport)
    line = report.data_lines[0]
    assert line.label == r"A \& B"
    assert line.value == r"x\_y"
