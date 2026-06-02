"""Tests for the static document analysis."""

from pytex.commands.builtin import Label, Ref
from pytex.commands.cleveref import Cref
from pytex.model.concat import Concat
from pytex.model.image import IncludeImage
from pytex.model.raw import Raw
from pytex_analyze import Severity, analyze


def test_clean_document_has_no_issues():
    assert analyze(Concat(Label("a"), Ref("a"))) == []


def test_undefined_reference_is_warned():
    issues = analyze(Ref("ghost"))
    assert len(issues) == 1
    assert issues[0].severity is Severity.WARNING
    assert "ghost" in issues[0].message


def test_duplicate_label_is_warned():
    issues = analyze(Concat(Label("dup"), Label("dup")))
    assert any(i.severity is Severity.WARNING and "dup" in i.message for i in issues)


def test_cref_comma_separated_labels_resolve():
    # Cref("a", "b") references two labels; both defined -> no issue.
    assert analyze(Concat(Label("a"), Label("b"), Cref("a", "b"))) == []


def test_cref_undefined_label_is_warned():
    issues = analyze(Concat(Label("a"), Cref("a", "b")))
    assert [i.message for i in issues if "b" in i.message]


def test_missing_image_is_error(tmp_path):
    issues = analyze(IncludeImage(str(tmp_path / "nope.png")))
    assert len(issues) == 1
    assert issues[0].severity is Severity.ERROR
    assert "not found" in issues[0].message


def test_existing_image_is_ok(tmp_path):
    img = tmp_path / "real.png"
    _ = img.write_bytes(b"\x89PNG")
    assert analyze(IncludeImage(str(img))) == []


def test_label_inside_raw_text_is_not_a_reference():
    # A label name only counts when carried by a \label control sequence,
    # not when it appears in arbitrary text.
    assert analyze(Raw(r"see \ref{x}")) == []
