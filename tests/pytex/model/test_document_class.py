from pytex.model.document_class import DocumentClass


def test_no_options():
    assert DocumentClass("article").rendered == r"\documentclass{article}"


def test_flag_only_option():
    out = DocumentClass("article", {"a4paper"}).rendered
    assert out == r"\documentclass[a4paper]{article}"


def test_key_value_option():
    out = DocumentClass("article", {("fontsize", "12pt")}).rendered
    assert out == r"\documentclass[fontsize=12pt]{article}"


def test_mixed_options():
    out = DocumentClass("article", {"a4paper", ("fontsize", "12pt")}).rendered
    assert "a4paper" in out and "fontsize=12pt" in out
    assert out.startswith(r"\documentclass[") and out.endswith("{article}")


def test_empty_options_no_brackets():
    assert "[" not in DocumentClass("article", set()).rendered
