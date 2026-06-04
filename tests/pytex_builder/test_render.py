"""End-to-end tests for the render stage of the build chain.

Covers every input kind get_tex_node accepts (.tex, .py, .md) plus the
error paths in _render_python. No tectonic/compile involved.
"""

import pytest

import pytex_builder.render as render_mod
from pytex_builder.render import _render_python, get_tex_node, render_input
from pytex_builder.tectonic import BuildError


def test_tex_input_is_wrapped_and_rendered(tmp_path):
    src = tmp_path / "doc.tex"
    _ = src.write_text(r"\section{Hi}")
    assert render_input(src) == r"\section{Hi}"


def test_py_input_renders_pytex_variable(tmp_path):
    src = tmp_path / "doc.py"
    _ = src.write_text("from pytex.model.raw import Raw\n__pytex__ = Raw(r'\\hello')\n")
    assert render_input(src) == r"\hello"


def test_py_input_can_import_siblings(tmp_path):
    _ = (tmp_path / "helper.py").write_text("VALUE = r'\\fromsibling'\n")
    src = tmp_path / "doc.py"
    _ = src.write_text(
        "from pytex.model.raw import Raw\n"
        "from helper import VALUE\n"
        "__pytex__ = Raw(VALUE)\n"
    )
    assert render_input(src) == r"\fromsibling"


def test_py_without_pytex_variable_raises(tmp_path):
    src = tmp_path / "doc.py"
    _ = src.write_text("x = 1\n")
    with pytest.raises(BuildError, match="defines no '__pytex__'"):
        _render_python(src)


def test_py_with_non_tex_pytex_raises(tmp_path):
    src = tmp_path / "doc.py"
    _ = src.write_text("__pytex__ = 42\n")
    with pytest.raises(BuildError, match="expected a TeX node"):
        _render_python(src)


def test_py_import_error_is_wrapped(tmp_path):
    src = tmp_path / "doc.py"
    _ = src.write_text("raise RuntimeError('boom')\n")
    with pytest.raises(BuildError, match=r"error while importing doc\.py: boom"):
        _render_python(src)


# -- t-string SyntaxError hint (P5b) ---------------------------------------


def _force_py313(monkeypatch):
    monkeypatch.setattr(
        render_mod.sys, "version_info", (3, 13, 0, "final", 0), raising=False
    )


def test_tstring_syntaxerror_hints_python_314(monkeypatch, tmp_path):
    # A t-string plus a trailing parse error -> SyntaxError on any interpreter.
    # On <3.14 the message must point at the t-string / Python 3.14 requirement.
    src = tmp_path / "doc.py"
    _ = src.write_text('__pytex__ = t"{x}"\n(\n')
    _force_py313(monkeypatch)
    with pytest.raises(BuildError) as exc:
        _render_python(src)
    message = str(exc.value)
    assert "Python 3.14" in message
    assert "t-string" in message
    assert "3.13" in message


def test_plain_syntaxerror_without_tstring_gets_no_hint(monkeypatch, tmp_path):
    # A syntax error with no t-string must not gain the (misleading) 3.14 hint.
    src = tmp_path / "doc.py"
    _ = src.write_text("def (:\n")
    _force_py313(monkeypatch)
    with pytest.raises(BuildError) as exc:
        _render_python(src)
    assert "Python 3.14" not in str(exc.value)


def test_tstring_no_hint_on_python_314_plus(tmp_path):
    # On the real (>=3.14) interpreter a t-string parses; force a different
    # syntax error and confirm no spurious downgrade hint is appended.
    src = tmp_path / "doc.py"
    _ = src.write_text('__pytex__ = t"{x}"\n(\n')
    with pytest.raises(BuildError) as exc:
        _render_python(src)
    assert "needs\nPython 3.14" not in str(exc.value)
    assert "you are on Python" not in str(exc.value)


def test_markdown_input_becomes_document(tmp_path):
    src = tmp_path / "doc.md"
    _ = src.write_text("# Title\n\nSome text.\n")
    out = render_input(src)
    assert r"\documentclass" in out
    assert r"\section{Title}" in out


def test_unsupported_suffix_raises(tmp_path):
    src = tmp_path / "doc.rtf"
    _ = src.write_text("x")
    with pytest.raises(BuildError, match=r"unsupported input type '\.rtf'"):
        get_tex_node(src)


def test_get_tex_node_does_not_render(tmp_path):
    src = tmp_path / "doc.tex"
    _ = src.write_text(r"\emph{x}")
    node = get_tex_node(src)
    # A node is returned without forcing a render.
    assert node.rendered == r"\emph{x}"
