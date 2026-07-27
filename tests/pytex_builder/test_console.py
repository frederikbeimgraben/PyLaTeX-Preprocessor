"""Tests for the `Console` status writer: level tags, indentation, and color."""

from io import StringIO

from pytex_builder.console import Console


def _plain(monkeypatch) -> Console:
    monkeypatch.setenv("NO_COLOR", "1")
    return Console(StringIO())


def test_step_emits_arrow_tag(monkeypatch):
    c = _plain(monkeypatch)
    c.step("Rendering")
    assert c.stream.getvalue() == "==> Rendering\n"


def test_levels_use_expected_tags(monkeypatch):
    c = _plain(monkeypatch)
    c.note("n")
    c.warn("w")
    c.error("e")
    out = c.stream.getvalue()
    assert "note: n" in out
    assert "warning: w" in out
    assert "error: e" in out


def test_detail_and_hint_are_indented(monkeypatch):
    c = _plain(monkeypatch)
    c.detail("d")
    c.hint("h")
    out = c.stream.getvalue()
    assert "    d\n" in out
    assert "    cause: h\n" in out


def test_no_color_strips_ansi(monkeypatch):
    c = _plain(monkeypatch)
    c.error("boom")
    assert "\033[" not in c.stream.getvalue()


def test_force_color_emits_ansi(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setenv("PYTEX_FORCE_COLOR", "1")
    c = Console(StringIO())
    c.step("go")
    assert "\033[" in c.stream.getvalue()


def test_no_color_takes_precedence_over_force(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setenv("PYTEX_FORCE_COLOR", "1")
    c = Console(StringIO())
    c.step("go")
    assert "\033[" not in c.stream.getvalue()


def test_success_uses_arrow_tag(monkeypatch):
    c = _plain(monkeypatch)
    c.success("done")
    assert c.stream.getvalue() == "==> done\n"
