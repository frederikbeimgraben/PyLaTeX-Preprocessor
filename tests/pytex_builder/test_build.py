"""Tests for the CLI driver: arg parsing, the render-only flow, exit codes.

The build (tectonic) branch is never exercised here - only the render path,
which is hermetic. main()'s error handling is checked via its exit codes.
"""

from io import StringIO

import pytest

from pytex_api import TrustLevel
from pytex_builder.build import Config, _parse_args, _run, main
from pytex_builder.console import Console
from pytex_builder.tectonic import BuildError


def _console() -> Console:
    return Console(StringIO())


def test_main_version_prints_and_exits(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert "pytex" in capsys.readouterr().out


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


def test_main_tree_prints_node_tree_and_still_renders(tmp_path, capsys):
    src = tmp_path / "in.py"
    _ = src.write_text(
        "from pytex.commands.builtin import Section\n__pytex__ = Section('X')\n"
    )
    out = tmp_path / "in.out.tex"
    code = main([str(src), "-o", str(out), "--tree"])
    assert code == 0
    tree = capsys.readouterr().out
    assert r"ControlSequence \section" in tree
    assert "├──" in tree or "└──" in tree
    # --tree prints the tree but still renders the output.
    assert out.read_text() == r"\section{X}"


def test_default_optimize_keeps_output_identical(tmp_path):
    # The optimize pass (on by default) is render-equivalent: the produced
    # .tex must be byte-identical to the --force (no-optimize) output.
    src = tmp_path / "in.py"
    _ = src.write_text(
        "from pytex.model.concat import Concat\n"
        "from pytex.model.raw import Raw\n"
        "__pytex__ = Concat('a', Concat(Raw(''), Raw('\\\\newpage')), 'b')\n"
    )
    opt = tmp_path / "opt.tex"
    raw = tmp_path / "raw.tex"
    assert main([str(src), "-o", str(opt)]) == 0
    assert main([str(src), "-o", str(raw), "--force"]) == 0
    assert opt.read_text() == raw.read_text()


def test_main_analysis_blocks_missing_image(tmp_path):
    src = tmp_path / "in.py"
    _ = src.write_text(
        "from pytex.model.image import IncludeImage\n"
        "__pytex__ = IncludeImage('does-not-exist.png')\n"
    )
    out = tmp_path / "in.out.tex"
    # Default: pre-flight analysis aborts before writing the output.
    assert main([str(src), "-o", str(out)]) == 1
    assert not out.exists()
    # --force skips analysis and renders anyway.
    assert main([str(src), "-o", str(out), "--force"]) == 0
    assert out.exists()


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


def test_default_trust_level_is_trusted():
    cfg = _parse_args(["doc.tex"])
    assert cfg.trust is TrustLevel.TRUSTED


def test_untrusted_flag_selects_untrusted():
    cfg = _parse_args(["doc.tex", "--untrusted"])
    assert cfg.trust is TrustLevel.UNTRUSTED


def test_trust_level_selects_sandboxed():
    cfg = _parse_args(["doc.tex", "--trust-level", "sandboxed"])
    assert cfg.trust is TrustLevel.SANDBOXED


def test_untrusted_and_trust_level_are_mutually_exclusive():
    with pytest.raises(SystemExit):
        _ = _parse_args(["doc.tex", "--untrusted", "--trust-level", "trusted"])


def test_untrusted_blocks_python_exec(tmp_path, capsys):
    # A .py input executes arbitrary code on import; --untrusted must refuse it
    # at the trust gate, before exec_module ever runs.
    src = tmp_path / "evil.py"
    _ = src.write_text(
        "import pathlib\n"
        f"pathlib.Path({str(tmp_path / 'pwned')!r}).write_text('x')\n"
        "__pytex__ = ...\n"
    )
    out = tmp_path / "out.tex"
    code = main([str(src), "-o", str(out), "--untrusted"])
    assert code == 1
    assert not out.exists()
    # The malicious import side effect never ran.
    assert not (tmp_path / "pwned").exists()
    err = capsys.readouterr().err
    assert "error:" in err
    assert "TRUSTED" in err


def test_untrusted_blocks_shell_escape_package(tmp_path):
    # `minted` is the shell-escape vector; the untrusted policy rejects every
    # code/shell-surface package regardless of the allowlist.
    src = tmp_path / "in.tex"
    _ = src.write_text("\\usepackage{minted}\nhi\n")
    out = tmp_path / "out.tex"
    code = main([str(src), "-o", str(out), "--untrusted"])
    assert code == 1
    assert not out.exists()


def test_untrusted_tex_renders_with_replacements_inert(tmp_path):
    # A benign .tex still renders untrusted, but the pytex(...) replacement is
    # NOT evaluated - the marker survives verbatim instead of running code.
    src = tmp_path / "in.tex"
    _ = src.write_text(r"Today \iffalse{pytex(Today())}\fi.")
    out = tmp_path / "out.tex"
    code = main([str(src), "-o", str(out), "--untrusted"])
    assert code == 0
    text = out.read_text()
    assert "pytex(Today())" in text


def test_trusted_default_still_executes_py(tmp_path):
    # Regression guard: the default (no flag) path is unchanged and runs .py.
    src = tmp_path / "in.py"
    _ = src.write_text("from pytex.model.raw import Raw\n__pytex__ = Raw(r'\\hi')\n")
    out = tmp_path / "in.out.tex"
    assert main([str(src), "-o", str(out)]) == 0
    assert out.read_text() == r"\hi"


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
