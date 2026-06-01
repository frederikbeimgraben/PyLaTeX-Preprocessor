"""Tests for the CLI driver: arg parsing, the render-only flow, exit codes.

The build (tectonic) branch is never exercised here - only the render path,
which is hermetic. main()'s error handling is checked via its exit codes.
"""

from io import StringIO

import pytest

from pytex_builder.build import Config, _run, main
from pytex_builder.console import Console
from pytex_builder.tectonic import BuildError


def _console() -> Console:
    return Console(StringIO())


def test_run_renders_tex_to_output_file(tmp_path):
    src = tmp_path / "in.tex"
    _ = src.write_text(r"\section{X}")
    out = tmp_path / "out" / "in.out.tex"
    cfg = Config(
        input=src, output=out, build=False, build_dir=tmp_path / "b", shell_escape=True
    )
    _run(cfg, _console())
    assert out.read_text() == r"\section{X}"


def test_run_missing_input_raises_builderror(tmp_path):
    cfg = Config(
        input=tmp_path / "nope.tex",
        output=tmp_path / "o.tex",
        build=False,
        build_dir=tmp_path,
        shell_escape=True,
    )
    with pytest.raises(BuildError, match="input file does not exist"):
        _run(cfg, _console())


def test_main_render_only_returns_zero(tmp_path):
    src = tmp_path / "in.py"
    _ = src.write_text("from pytex.model.raw import Raw\n__pytex__ = Raw(r'\\hi')\n")
    out = tmp_path / "in.out.tex"
    code = main([str(src), "-o", str(out)])
    assert code == 0
    assert out.read_text() == r"\hi"


def test_main_missing_input_returns_one(tmp_path):
    code = main([str(tmp_path / "ghost.tex"), "-o", str(tmp_path / "o.tex")])
    assert code == 1


def test_main_unsupported_suffix_returns_one(tmp_path):
    src = tmp_path / "in.rtf"
    _ = src.write_text("x")
    code = main([str(src), "-o", str(tmp_path / "o.tex")])
    assert code == 1


def test_main_reports_error_to_console(tmp_path, capsys):
    _ = main([str(tmp_path / "ghost.tex"), "-o", str(tmp_path / "o.tex")])
    err = capsys.readouterr().err
    assert "error:" in err
    assert "input file does not exist" in err


def test_run_creates_output_parent_dirs(tmp_path):
    src = tmp_path / "in.tex"
    _ = src.write_text(r"\x")
    out = tmp_path / "deep" / "nested" / "in.out.tex"
    cfg = Config(
        input=src, output=out, build=False, build_dir=tmp_path, shell_escape=True
    )
    _run(cfg, _console())
    assert out.exists()


def test_run_render_only_skips_build_dir(tmp_path):
    src = tmp_path / "in.tex"
    _ = src.write_text(r"\x")
    build_dir = tmp_path / "build"
    cfg = Config(
        input=src,
        output=tmp_path / "in.out.tex",
        build=False,
        build_dir=build_dir,
        shell_escape=True,
    )
    _run(cfg, _console())
    # Render-only must not create the build directory.
    assert not build_dir.exists()
