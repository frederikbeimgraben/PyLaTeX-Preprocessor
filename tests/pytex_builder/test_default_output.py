from pathlib import Path

from pytex_builder.build import _default_output, _parse_args


def test_default_output_lives_in_build_dir():
    out = _default_output(Path("examples/report.tex.py"), Path("build"))
    assert out == Path("build/report.out.tex")


def test_default_output_strips_double_extension():
    assert _default_output(Path("a/b/paper.tex"), Path("out")) == Path("out/paper.out.tex")
    assert _default_output(Path("x.py"), Path("out")) == Path("out/x.out.tex")


def test_parse_args_defaults_output_to_build_dir():
    cfg = _parse_args(["examples/report.tex.py"])
    assert cfg.output == Path("build/report.out.tex")


def test_parse_args_default_output_follows_custom_build_dir():
    cfg = _parse_args(["foo.tex.py", "--build-dir", "dist"])
    assert cfg.output == Path("dist/foo.out.tex")


def test_explicit_output_overrides_build_dir():
    cfg = _parse_args(["foo.tex.py", "-o", "custom/here.tex"])
    assert cfg.output == Path("custom/here.tex")
