"""Tests that convert a whole Markdown meeting protocol, callouts included."""

import marko

from pytex_hsrtreport.document import HSRTReport
from pytex_hsrtreport.variants import Variant
from pytex_markdown.protocol import render_protocol
from pytex_markdown.protocol.convert import ProtocolConverter

_PARSER = marko.Markdown()


def _render_md(md: str, **meta) -> str:
    converter = ProtocolConverter(meta=meta)
    return converter.block(_PARSER.parse(md)).rendered


def test_beschluss_callout_becomes_decision_box():
    out = _render_md("> [!beschluss] Antrag angenommen\n> Einstimmig.")
    assert "Beschluss" in out
    assert "gavel" in out
    assert "Einstimmig" in out  # the text after the title line stays


def test_abstimmung_callout_parses_tally():
    out = _render_md("> [!abstimmung] Antrag\n> Ja: 12, Nein: 3, Enthaltung: 2")
    assert "vote-yea" in out
    # The converter parses the tally into a `VotingResults` box.
    assert "12" in out and "3" in out and "2" in out


def test_abstimmung_keeps_body_text_lines():
    # A line that is not the tally must stay as the body of the box.
    out = _render_md(
        "> [!abstimmung]\n> Beschlussvorschlag XY\n> Ja: 1, Nein: 2, Enthaltung: 3"
    )
    assert "Beschlussvorschlag XY" in out
    assert "vote-yea" in out


def test_aufgabe_callout():
    out = _render_md("> [!aufgabe] Doku schreiben")
    assert "Aufgabe" in out


def test_inline_shortcode_in_paragraph():
    out = _render_md("Beginn um {{time 9:00}}.", gremium="STUPA")
    assert "9:00" in out


def test_field_reference_uses_meta():
    out = _render_md("Gremium: {{gremium}}.", gremium="AStA")
    assert "AStA" in out


def test_github_callouts_still_work():
    out = _render_md("> [!note] Hinweis\n> Text.")
    assert "info-circle" in out  # the `InfoBox` of the base converter


def test_render_protocol_returns_hsrtreport():
    md = "---\ngremium: STUPA\n---\n\n# TOP 1\n\nText."
    doc = render_protocol(md)
    assert isinstance(doc, HSRTReport)
    assert doc.variant is Variant.STUPA
    assert doc.show_titlepage is True  # the HSRT title page carries the metadata


def test_render_protocol_variant_mapping():
    assert render_protocol("---\ngremium: asta\n---\n").variant is Variant.ASTA
    assert render_protocol("---\ngremium: stupa\n---\n").variant is Variant.STUPA
    # An unknown `gremium` value gives the STUPA variant.
    assert render_protocol("---\ngremium: foo\n---\n").variant is Variant.STUPA


def test_render_protocol_full_document():
    md = (
        "---\ngremium: STUPA\ndatum: 2026-06-15\nanwesend: [A, B]\n---\n\n"
        "# Begrüßung\n\nStart {{time 18:30}}, anwesend {{count anwesend}}.\n\n"
        "> [!beschluss] Angenommen\n"
    )
    out = render_protocol(md).rendered
    assert r"\documentclass" in out
    # The title uses the German date format, not the frontmatter format.
    assert "Protokoll der Sitzung des STUPA vom 15.06.2026" in out
    assert "Datum" in out and "2026-06-15" in out  # metadata as data lines
    assert "18:30" in out
    assert "Beschluss" in out
    assert r"\section{Begr" in out  # an agenda item is a numbered section


def test_title_is_descriptive_with_german_date():
    from pytex_markdown.protocol.document import _title

    assert (
        _title({"gremium": "STUPA", "datum": "2026-06-15"})
        == "Protokoll der Sitzung des STUPA vom 15.06.2026"
    )
    assert _title({"gremium": "AStA"}) == "Protokoll der Sitzung des AStA"
    assert _title({}) == "Sitzungsprotokoll"


def test_data_lines_cover_metadata():
    from pytex_markdown.protocol.document import _data_lines

    meta = {
        "datum": "2026-06-15",
        "beginn": "18:30",
        "ende": "20:00",
        "ort": "Aula",
        "sitzungsleitung": "A. Muster",
        "anwesend": ["A", "B", "C"],
    }
    labels = [line.label for line in _data_lines(meta)]
    assert labels == ["Datum", "Zeit", "Ort", "Sitzungsleitung", "Anwesend (3)"]


def test_agenda_items_numbered_as_tops():
    out = render_protocol("---\ngremium: STUPA\n---\n\n# TOP\n").rendered
    assert r"\renewcommand*{\thesection}{TOP~\arabic{section}}" in out
