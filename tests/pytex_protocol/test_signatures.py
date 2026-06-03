import marko

from pytex_markdown.protocol import render_protocol
from pytex_markdown.protocol.convert import ProtocolConverter
from pytex_markdown.protocol.signatures import SignatureLines, signature_block_from_meta

_PARSER = marko.Markdown()


def test_signature_lines_render_rule_name_role():
    out = SignatureLines(("Sitzungsleitung", "A. Muster")).rendered
    assert "Unterschriften" in out
    assert r"\rule" in out
    assert "A. Muster" in out
    assert "Sitzungsleitung" in out


def test_bare_role_leaves_blank_name_line():
    out = SignatureLines("Vorstand").rendered
    assert "Vorstand" in out
    assert r"~\\" in out  # blank name placeholder above the role


def test_no_signers_renders_empty():
    assert SignatureLines().rendered == ""


def test_block_from_meta_pulls_names_by_role():
    meta = {
        "sitzungsleitung": "A. Muster",
        "protokoll": "B. Beispiel",  # Schriftführung maps to the protokoll key
        "vorstand": "C. Chef",
        "unterschriften": ["Sitzungsleitung", "Schriftführung", "Vorstand"],
    }
    block = signature_block_from_meta(meta)
    assert block is not None
    out = block.rendered
    assert "A. Muster" in out and "B. Beispiel" in out and "C. Chef" in out


def test_block_from_meta_absent_returns_none():
    assert signature_block_from_meta({"gremium": "STUPA"}) is None


def test_render_protocol_appends_signatures():
    md = (
        "---\ngremium: STUPA\nsitzungsleitung: A. Muster\n"
        "unterschriften: [Sitzungsleitung, Vorstand]\n---\n\n# TOP\n"
    )
    out = render_protocol(md).rendered
    assert r"\section*{Unterschriften}" in out
    assert "A. Muster" in out


def test_render_protocol_no_signatures_without_key():
    out = render_protocol("---\ngremium: STUPA\n---\n\n# TOP\n").rendered
    assert "Unterschriften" not in out


def test_unterschriften_callout():
    md = (
        "> [!unterschriften]\n"
        "> Sitzungsleitung: A. Muster\n"
        "> Schriftführung: B. Beispiel"
    )
    out = ProtocolConverter().block(_PARSER.parse(md)).rendered
    assert "Unterschriften" in out
    assert "A. Muster" in out and "Schriftführung" in out
