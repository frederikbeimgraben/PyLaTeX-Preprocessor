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
    INSTALL_HINT,
    BuildError,
    _biber_candidates,
    _biber_sources,
    _download_to,
    _extract_biber_binary,
    _resolve_cache_dir,
    biber_for_build,
    ensure_tectonic,
    run_makeindex,
)


def _console() -> Console:
    return Console(StringIO())


# -- persistent binary cache dir (P4) --------------------------------------


def test_cache_dir_prefers_xdg(monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", "/xdg")
    path, warning = _resolve_cache_dir()
    assert path == Path("/xdg/pytex")
    assert warning is None


def test_cache_dir_falls_back_to_home_cache(monkeypatch):
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
    monkeypatch.setattr(tec.Path, "home", classmethod(lambda _cls: Path("/home/u")))
    path, warning = _resolve_cache_dir()
    assert path == Path("/home/u/.cache/pytex")
    assert warning is None


def test_cache_dir_home_unset_falls_back_to_tempdir_with_warning(monkeypatch):
    # HOME unset -> Path.home() raises; cache must degrade, never crash.
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)

    def _boom(_cls):
        raise RuntimeError("Could not determine home directory")

    monkeypatch.setattr(tec.Path, "home", classmethod(_boom))
    monkeypatch.setattr(tec.tempfile, "gettempdir", lambda: "/tmp")
    path, warning = _resolve_cache_dir()
    assert path == Path("/tmp/pytex-tectonic")
    assert warning is not None
    assert "HOME" in warning


def test_cache_dir_not_under_tempdir_by_default(monkeypatch):
    # The whole point of P4: a normal session caches in $HOME, not /tmp.
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
    monkeypatch.setattr(tec.Path, "home", classmethod(lambda _cls: Path("/home/u")))
    path, _warning = _resolve_cache_dir()
    assert "/tmp" not in str(path)


# -- download failure hint (P5a) -------------------------------------------


def test_ensure_tectonic_missing_curl_hints_manual_install(monkeypatch):
    monkeypatch.setattr(tec.shutil, "which", lambda _name: None)
    monkeypatch.setattr(tec, "_cached_binary", lambda: Path("/nope/tectonic"))
    with pytest.raises(BuildError) as exc:
        ensure_tectonic(_console())
    assert INSTALL_HINT in str(exc.value)


def test_ensure_tectonic_download_failure_hints_manual_install(monkeypatch, tmp_path):
    # tectonic absent (so it downloads), curl+sh present, script exits non-zero.
    monkeypatch.setattr(
        tec.shutil,
        "which",
        lambda name: None if name == "tectonic" else f"/usr/bin/{name}",
    )
    monkeypatch.setattr(tec, "_cached_binary", lambda: tmp_path / "tectonic")
    monkeypatch.setattr(tec, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(
        tec.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(returncode=1, stdout="", stderr="boom"),
    )
    with pytest.raises(BuildError) as exc:
        ensure_tectonic(_console())
    assert INSTALL_HINT in str(exc.value)
    assert "boom" in str(exc.value)


def test_builderror_is_runtimeerror():
    assert issubclass(BuildError, RuntimeError)


@pytest.mark.parametrize(
    ("system", "machine", "first_asset"),
    [
        ("Linux", "x86_64", "biber-2.17-linux_x86_64-musl.tar.gz"),
        ("Linux", "aarch64", "biber-2.17-linux_aarch64.tar.gz"),
        ("Darwin", "arm64", "biber-2.17-darwin_universal.tar.gz"),
        ("Darwin", "x86_64", "biber-2.17-darwin_universal.tar.gz"),
        ("Windows", "AMD64", "biber-2.17-MSWIN64.zip"),
    ],
)
def test_biber_candidates_first(monkeypatch, system, machine, first_asset):
    monkeypatch.setattr(tec.platform, "system", lambda: system)
    monkeypatch.setattr(tec.platform, "machine", lambda: machine)
    assert _biber_candidates("2.17")[0][2] == first_asset


def test_biber_candidates_linux_x86_64_prefers_musl_then_glibc(monkeypatch):
    # The static musl build (no libnsl.so.1 dependency) is tried before glibc.
    monkeypatch.setattr(tec.platform, "system", lambda: "Linux")
    monkeypatch.setattr(tec.platform, "machine", lambda: "x86_64")
    assets = [asset for _, _, asset in _biber_candidates("2.17")]
    assert assets == [
        "biber-2.17-linux_x86_64-musl.tar.gz",
        "biber-2.17-linux_x86_64.tar.gz",
    ]


def test_biber_candidates_macos_subdir_moved_at_217(monkeypatch):
    monkeypatch.setattr(tec.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(tec.platform, "machine", lambda: "x86_64")
    assert _biber_candidates("2.16")[0][0] == "OSX_Intel"
    assert _biber_candidates("2.17")[0][0] == "MacOS"


def test_biber_candidates_unsupported_raises(monkeypatch):
    monkeypatch.setattr(tec.platform, "system", lambda: "Plan9")
    monkeypatch.setattr(tec.platform, "machine", lambda: "pdp11")
    with pytest.raises(BuildError, match="unsupported platform"):
        _biber_candidates("2.17")


def test_biber_sources_mirror_before_sourceforge_per_candidate(monkeypatch):
    monkeypatch.setattr(tec.platform, "system", lambda: "Linux")
    monkeypatch.setattr(tec.platform, "machine", lambda: "x86_64")
    sources = _biber_sources("2.17")
    # musl (mirror, SourceForge) then glibc (mirror, SourceForge)
    assert len(sources) == 4
    urls = [url for url, _ in sources]
    assert "github.com" in urls[0] and "musl" in urls[0]
    assert "sourceforge.net" in urls[1]
    assert "github.com" in urls[2] and urls[2].endswith(
        "biber-2.17-linux_x86_64.tar.gz"
    )
    assert "sourceforge.net" in urls[3]
    # every mirrored platform now carries a pinned checksum
    assert all(sha for _, sha in sources)


def test_is_biber_member_selects_binary_skips_appledouble():
    assert tec._is_biber_member("biber")
    assert tec._is_biber_member("biber.exe")
    assert tec._is_biber_member("dir/biber-linux_x86_64-musl")
    assert not tec._is_biber_member("._biber")
    assert not tec._is_biber_member("README")


def test_extract_biber_from_tar_picks_largest_biber(tmp_path):
    import io
    import tarfile

    archive = tmp_path / "a.tar.gz"
    with tarfile.open(archive, "w:gz") as tf:
        for name, data in [("._biber", b"junk"), ("biber", b"REALBINARY")]:
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
    assert _extract_biber_binary(archive, "x") == b"REALBINARY"


def test_extract_biber_from_zip(tmp_path):
    import zipfile

    archive = tmp_path / "a.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("biber.exe", b"WINBINARY")
    assert _extract_biber_binary(archive, "x") == b"WINBINARY"


def test_extract_biber_missing_raises(tmp_path):
    import io
    import tarfile

    archive = tmp_path / "a.tar.gz"
    with tarfile.open(archive, "w:gz") as tf:
        info = tarfile.TarInfo("README")
        info.size = 1
        tf.addfile(info, io.BytesIO(b"x"))
    with pytest.raises(BuildError, match="not found"):
        _extract_biber_binary(archive, "x")


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


def testbiber_for_build_no_bcf_returns_none(tmp_path):
    assert biber_for_build(tmp_path, "job", _console()) is None


def testbiber_for_build_unknown_version_warns(tmp_path):
    bcf = tmp_path / "job.bcf"
    _ = bcf.write_text('<controlfile version="9.99"/>')
    console = Console(StringIO())
    assert biber_for_build(tmp_path, "job", console) is None
    assert "unknown BCF version" in console.stream.getvalue()


def testbiber_for_build_matches_system_biber(monkeypatch, tmp_path):
    bcf = tmp_path / "job.bcf"
    _ = bcf.write_text('<controlfile version="3.8"/>')  # -> biber 2.17
    monkeypatch.setattr(tec.shutil, "which", lambda name: "/usr/bin/biber")
    monkeypatch.setattr(
        tec.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(stdout="biber version: 2.17\n", returncode=0),
    )
    assert biber_for_build(tmp_path, "job", _console()) == Path("/usr/bin/biber")


def testbiber_for_build_malformed_bcf_returns_none(tmp_path):
    bcf = tmp_path / "job.bcf"
    _ = bcf.write_text("not xml <<<")
    assert biber_for_build(tmp_path, "job", _console()) is None


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
