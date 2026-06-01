from pytex_protocol.header import ProtocolHeader, header_from_meta

META = {
    "gremium": "STUPA",
    "datum": "2026-06-15",
    "beginn": "18:30",
    "ende": "20:00",
    "ort": "Aula",
    "sitzungsleitung": "A. Muster",
    "anwesend": ["A", "B", "C"],
    "entschuldigt": ["D"],
}


def test_header_from_meta_collects_fields():
    header = header_from_meta(META)
    assert header.gremium == "STUPA"
    assert header.fields["ort"] == "Aula"
    assert header.attendance["anwesend"] == ["A", "B", "C"]


def test_header_title():
    assert header_from_meta(META).title == "STUPA — Protokoll"
    assert ProtocolHeader().title == "Protokoll"


def test_header_render_shows_counts_and_datetime():
    out = header_from_meta(META).rendered
    assert "STUPA — Protokoll" in out
    assert "2026-06-15" in out
    assert "18:30" in out and "20:00" in out
    assert "Anwesend (3)" in out
    assert "Entschuldigt (1)" in out


def test_gaeste_umlaut_alias():
    header = header_from_meta({"gremium": "AStA", "gäste": ["H. Gast"]})
    assert header.attendance["gaeste"] == ["H. Gast"]
