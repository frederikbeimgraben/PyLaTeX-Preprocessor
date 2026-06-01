"""Tests for the tectonic/biber/makeindex helpers.

External tools are never actually run: shutil.which and subprocess.run are
monkeypatched so the platform/version/glossary logic is exercised in isolation.
"""

from io import StringIO
from pathlib import Path
from types import SimpleNamespace

import pytest

import pytex_builder.tectonic as tec
from pytex_builder.console import Console
from pytex_builder.tectonic import (
    BuildError,
    _biber_for_build,
    _biber_sf_path,
    _biber_sources,
    _download_to,
    _mirror_asset,
    ensure_tectonic,
    run_makeindex,
)


def _console() -> Console:
    return Console(StringIO())


def test_builderror_is_runtimeerror():
    assert issubclass(BuildError, RuntimeError)


@pytest.mark.parametrize(
    ("system", "machine", "expected_dir", "expected_file"),
    [
        ("Linux", "x86_64", "Linux", "biber-linux_x86_64.tar.gz"),
        ("Linux", "aarch64", "Linux-musl", "biber-linuxmusl_aarch64.tar.gz"),
        ("Darwin", "arm64", "MacOS", "biber-darwin_arm64.tar.gz"),
        ("Darwin", "x86_64", "MacOS", "biber-darwin_x86_64.tar.gz"),
        ("Windows", "AMD64", "Windows", "biber-windows_x86_64.zip"),
    ],
)
def test_biber_sf_path(monkeypatch, system, machine, expected_dir, expected_file):
    monkeypatch.setattr(tec.platform, "system", lambda: system)
    monkeypatch.setattr(tec.platform, "machine", lambda: machine)
    assert _biber_sf_path() == (expected_dir, expected_file)


def test_biber_sf_path_unsupported_raises(monkeypatch):
    monkeypatch.setattr(tec.platform, "system", lambda: "Plan9")
    monkeypatch.setattr(tec.platform, "machine", lambda: "pdp11")
    with pytest.raises(BuildError, match="unsupported platform"):
        _biber_sf_path()


def test_mirror_asset_inserts_version():
    assert (
        _mirror_asset("2.17", "biber-linux_x86_64.tar.gz")
        == "biber-2.17-linux_x86_64.tar.gz"
    )


def test_biber_sources_mirror_first_with_known_sha(monkeypatch):
    monkeypatch.setattr(tec.platform, "system", lambda: "Linux")
    monkeypatch.setattr(tec.platform, "machine", lambda: "x86_64")
    sources = _biber_sources("2.17")
    assert len(sources) == 2
    (mirror_url, mirror_sha), (sf_url, sf_sha) = sources
    assert "github.com" in mirror_url and "biber-2.17-linux_x86_64.tar.gz" in mirror_url
    assert "sourceforge.net" in sf_url
    # checksum is the same content regardless of source
    assert mirror_sha == sf_sha == tec.BIBER_SHA256["biber-2.17-linux_x86_64.tar.gz"]


def test_biber_sources_unknown_platform_has_no_sha(monkeypatch):
    monkeypatch.setattr(tec.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(tec.platform, "machine", lambda: "arm64")
    sources = _biber_sources("2.17")
    assert all(sha is None for _, sha in sources)


def test_download_to_rejects_checksum_mismatch(monkeypatch, tmp_path):
    dest = tmp_path / "biber.download"

    def fake_run(cmd, **kwargs):
        dest.write_bytes(b"not the real binary")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(tec.subprocess, "run", fake_run)
    console = Console(StringIO())
    ok = _download_to("https://example/biber.tar.gz", dest, "deadbeef", console)
    assert ok is False
    assert not dest.exists()
    assert "checksum mismatch" in console.stream.getvalue()


def test_download_to_accepts_matching_checksum(monkeypatch, tmp_path):
    dest = tmp_path / "biber.download"
    payload = b"hello biber"
    import hashlib as _hl

    sha = _hl.sha256(payload).hexdigest()

    def fake_run(cmd, **kwargs):
        dest.write_bytes(payload)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(tec.subprocess, "run", fake_run)
    assert _download_to("https://example/b.tar.gz", dest, sha, _console()) is True
    assert dest.exists()


def test_download_to_curl_failure_returns_false(monkeypatch, tmp_path):
    dest = tmp_path / "biber.download"
    monkeypatch.setattr(
        tec.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(returncode=22, stdout="", stderr="404"),
    )
    assert _download_to("https://example/b.tar.gz", dest, None, _console()) is False


def test_ensure_tectonic_uses_path_binary(monkeypatch):
    monkeypatch.setattr(tec.shutil, "which", lambda name: "/usr/bin/tectonic")
    assert ensure_tectonic(_console()) == Path("/usr/bin/tectonic")


def test_ensure_tectonic_uses_cached_binary(monkeypatch, tmp_path):
    monkeypatch.setattr(tec.shutil, "which", lambda name: None)
    cached = tmp_path / "tectonic"
    _ = cached.write_text("#!/bin/sh\n")
    monkeypatch.setattr(tec, "_cached_binary", lambda: cached)
    assert ensure_tectonic(_console()) == cached


def test_biber_for_build_no_bcf_returns_none(tmp_path):
    assert _biber_for_build(tmp_path, "job", _console()) is None


def test_biber_for_build_unknown_version_warns(tmp_path):
    bcf = tmp_path / "job.bcf"
    _ = bcf.write_text('<controlfile version="9.99"/>')
    console = Console(StringIO())
    assert _biber_for_build(tmp_path, "job", console) is None
    assert "unknown BCF version" in console.stream.getvalue()


def test_biber_for_build_matches_system_biber(monkeypatch, tmp_path):
    bcf = tmp_path / "job.bcf"
    _ = bcf.write_text('<controlfile version="3.8"/>')  # -> biber 2.17
    monkeypatch.setattr(tec.shutil, "which", lambda name: "/usr/bin/biber")
    monkeypatch.setattr(
        tec.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(stdout="biber version: 2.17\n", returncode=0),
    )
    assert _biber_for_build(tmp_path, "job", _console()) == Path("/usr/bin/biber")


def test_biber_for_build_malformed_bcf_returns_none(tmp_path):
    bcf = tmp_path / "job.bcf"
    _ = bcf.write_text("not xml <<<")
    assert _biber_for_build(tmp_path, "job", _console()) is None


def test_run_makeindex_no_targets_returns_false(tmp_path):
    # No .glo/.acn and no .ist style file present.
    assert run_makeindex("job", tmp_path, console=_console()) is False


def test_run_makeindex_missing_makeindex_warns(monkeypatch, tmp_path):
    _ = (tmp_path / "job.glo").write_text("x")
    _ = (tmp_path / "job.ist").write_text("x")
    monkeypatch.setattr(tec.shutil, "which", lambda name: None)
    console = Console(StringIO())
    assert run_makeindex("job", tmp_path, console=console) is False
    assert "makeindex" in console.stream.getvalue()


def test_run_makeindex_success_returns_true(monkeypatch, tmp_path):
    _ = (tmp_path / "job.glo").write_text("x")
    _ = (tmp_path / "job.ist").write_text("x")
    monkeypatch.setattr(tec.shutil, "which", lambda name: "/usr/bin/makeindex")
    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(tec.subprocess, "run", fake_run)
    assert run_makeindex("job", tmp_path, console=_console()) is True
    assert calls and calls[0][0] == "/usr/bin/makeindex"


def test_run_makeindex_failure_returns_false(monkeypatch, tmp_path):
    _ = (tmp_path / "job.glo").write_text("x")
    _ = (tmp_path / "job.ist").write_text("x")
    monkeypatch.setattr(tec.shutil, "which", lambda name: "/usr/bin/makeindex")
    monkeypatch.setattr(
        tec.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(returncode=1, stdout="", stderr="bad"),
    )
    assert run_makeindex("job", tmp_path, console=_console()) is False
