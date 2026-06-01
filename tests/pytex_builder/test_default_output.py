from pathlib import Path

from pytex_builder.build import _default_output, _parse_args, _slug


def test_default_output_lives_in_build_dir():
    out = _default_output(Path("examples/report.tex.py"), Path("build"))
    assert out == Path("build/report.out.tex")


def test_default_output_strips_double_extension():
    assert _default_output(Path("a/b/paper.tex"), Path("out")) == Path(
        "out/paper.out.tex"
    )
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


def test_default_output_slugifies_spaces():
    # Spaces in the stem would break the TeX jobname (biber/.bcf); collapse them.
    out = _default_output(Path("Meetings/2026-06-15 STUPA.md"), Path("build"))
    assert out == Path("build/2026-06-15_STUPA.md.out.tex")
    assert " " not in out.name


def test_slug_collapses_whitespace_and_drops_hostile_chars():
    assert _slug("2026-06-15 STUPA") == "2026-06-15_STUPA"
    assert _slug("a  b\tc") == "a_b_c"
    assert _slug("wö!rd?:(x).md") == "wörd x.md".replace(" ", "")
    assert _slug("   ") == "document"
