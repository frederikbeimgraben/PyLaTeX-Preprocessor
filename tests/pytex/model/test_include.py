from pytex.model.include import IncludeTeX
from pytex.model.raw import Raw


def test_reads_file_contents(tmp_path):
    p = tmp_path / "x.tex"
    p.write_text(r"\section{hi}")
    inc = IncludeTeX(p)
    assert isinstance(inc, Raw)
    assert inc.rendered == r"\section{hi}"


def test_evaluates_pytex_replacements(tmp_path):
    p = tmp_path / "x.tex"
    p.write_text(r"value=\iffalse{ pytex(1+2) }\fi")
    assert IncludeTeX(p).rendered == "value=3"


def test_namespace_passed_through(tmp_path):
    p = tmp_path / "x.tex"
    p.write_text(r"\iffalse{ pytex(name) }\fi")
    inc = IncludeTeX(p, namespace={"name": "Frederik"})
    assert inc.rendered == "Frederik"


def test_allow_replacements_false(tmp_path):
    p = tmp_path / "x.tex"
    content = r"value=\iffalse{ pytex(1+2) }\fi"
    p.write_text(content)
    inc = IncludeTeX(p, allow_replacements=False)
    assert inc.rendered == content


def test_accepts_str_path(tmp_path):
    p = tmp_path / "x.tex"
    p.write_text("hello")
    assert IncludeTeX(str(p)).rendered == "hello"


def test_missing_file_raises(tmp_path):
    import pytest

    with pytest.raises(FileNotFoundError):
        IncludeTeX(tmp_path / "missing.tex")
