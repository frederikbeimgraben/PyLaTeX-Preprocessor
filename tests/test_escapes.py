"""Tests for the inline pytex escape syntax in Raw / IncludeTeX."""

from pathlib import Path

from pytex import Bold, IncludeTeX, Raw
from pytex.model.escapes import evaluate_escapes


class TestEvaluateEscapes:
    def test_percent_form_with_tex_result(self):
        out = evaluate_escapes(r'%{ pytex (Bold("hi")) }%')
        assert out == Bold(Raw("hi")).serialize()

    def test_iffalse_form(self):
        assert evaluate_escapes(r'\iffalse{ pytex ("X" * 3) }\fi') == "XXX"

    def test_arithmetic_expression(self):
        assert evaluate_escapes(r"%{ pytex (1 + 2 + 3) }%") == "6"

    def test_extra_namespace(self):
        out = evaluate_escapes(r"%{ pytex (n * 2) }%", {"n": 21})
        assert out == "42"

    def test_nested_parens(self):
        assert evaluate_escapes(r"%{ pytex (((1 + 2)) * (3)) }%") == "9"

    def test_literal_segments_space_escaped(self):
        out = evaluate_escapes("a b %{ pytex (1) }% c d", escape_spaces=True)
        assert out == "a~b~1~c~d"

    def test_no_escape_is_passthrough(self):
        assert evaluate_escapes("just text", escape_spaces=False) == "just text"

    def test_parens_inside_string_literal_not_miscounted(self):
        assert evaluate_escapes(r'%{ pytex (")(" + "!") }%') == ")(!"


class TestRawEscapes:
    def test_raw_evaluates_escape(self):
        r = Raw(r'x %{ pytex (Bold("y")) }%', escape_spaces=False)
        assert "\\textbf{y}" in r.serialize()

    def test_raw_namespace_field(self):
        r = Raw(r"%{ pytex (val) }%", escape_spaces=False, namespace={"val": "Z"})
        assert r.serialize() == "Z"

    def test_plain_raw_unchanged(self):
        assert Raw("hello world").serialize() == "hello~world"


class TestIncludeTeXEscapes:
    def test_inlines_and_evaluates(self, tmp_path: Path):
        f = tmp_path / "chapter.tex"
        f.write_text('Intro %{ pytex (Bold("bold")) }% done')
        out = IncludeTeX(f).serialize()
        assert "\\textbf{bold}" in out
        assert "\\input" not in out

    def test_missing_file_falls_back_to_input(self):
        out = IncludeTeX("nonexistent/file.tex").serialize()
        assert out == "\\input{nonexistent/file}"
