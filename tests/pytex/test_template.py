"""Tests for `tex(t"...")` with PEP 750 template strings.

This file uses t-string syntax. Only Python 3.14 or later can parse it. On an
older Python, the root conftest excludes the file with `collect_ignore_glob`.
"""

from pytex.commands.builtin import Bold, Section
from pytex.model.concat import Concat
from pytex.template import tex


def test_plain_value_is_escaped():
    name = "Q&A 50%"
    assert tex(t"Comment: {name}").rendered == r"Comment: Q\&A 50\%"


def test_literal_latex_is_verbatim():
    # The static parts are author LaTeX. `{{` and `}}` are literal braces.
    assert tex(rt"\textbf{{x}} and 50\%").rendered == r"\textbf{x} and 50\%"


def test_tex_node_is_spliced_unescaped():
    assert tex(t"{Bold('hi')}").rendered == r"\textbf{hi}"


def test_mixed_node_and_text():
    title = "A&B"
    out = tex(t"{Section('S')} — {title}")
    assert out.rendered == r"\section{S} — A\&B"


def test_result_is_a_concat():
    assert isinstance(tex(t"a{1}b"), Concat)


def test_none_renders_nothing():
    assert tex(t"a{None}b").rendered == "ab"


def test_list_interpolation_maps_each_element():
    assert tex(t"{[Bold('a'), Bold('b')]}").rendered == r"\textbf{a}\textbf{b}"


def test_nested_template_recurses():
    value = "x&y"
    assert tex(t"[{t'{value}'}]").rendered == r"[x\&y]"


def test_format_spec_then_escape():
    ratio = 0.5
    # The format spec turns 0.5 into `50%` first. PyTeX then escapes the `%`.
    assert tex(t"{ratio:.0%}").rendered == r"50\%"


def test_conversion_is_applied():
    value = "a"
    assert tex(t"{value!r}").rendered == r"'a'"


def test_empty_template_is_empty():
    assert tex(t"").rendered == ""
