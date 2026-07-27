"""Tests for `pytex-tex2py`, which serializes a `.tex` file to a `.tex.py` file."""

from pathlib import Path

from pytex.model.raw import Raw
from pytex_analyze import Optimize
from pytex_builder.tex2py import _output_path, main, to_python

_SAMPLE = (
    "% a header comment\n"
    r"\documentclass{article}\begin{document}"
    r"Today is \iffalse{pytex(Today())}\fi. "
    r"Math: $\iffalse{pytex(Frac('1', '2'))}\fi$."
    r"\end{document}"
)


def _rebuild(source: str):
    namespace: dict[str, object] = {}
    exec(source, namespace)
    return namespace["__pytex__"]


def test_to_python_roundtrips_rendering():
    node = Optimize(Raw(_SAMPLE))
    rebuilt = _rebuild(to_python(node))
    assert rebuilt.rendered == node.rendered


def test_generated_source_has_pytex_var_and_imports():
    source = to_python(Optimize(Raw(_SAMPLE)))
    assert "__pytex__ =" in source
    assert "from pytex.model.comment import Comment" in source
    assert source.startswith("from ")


def test_output_path_default_naming():
    assert _output_path(Path("doc.tex")).name == "doc.tex.py"
    assert _output_path(Path("notes.py.tex")).name == "notes.tex.py"


def test_main_writes_file_and_roundtrips(tmp_path):
    src = tmp_path / "in.tex"
    _ = src.write_text(_SAMPLE)
    out = tmp_path / "in.tex.py"
    assert main([str(src), "-o", str(out)]) == 0
    rebuilt = _rebuild(out.read_text())
    assert rebuilt.rendered == Optimize(Raw(_SAMPLE)).rendered


def test_main_missing_input_returns_one(tmp_path):
    assert main([str(tmp_path / "ghost.tex")]) == 1
