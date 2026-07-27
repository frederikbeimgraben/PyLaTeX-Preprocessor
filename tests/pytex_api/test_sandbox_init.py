"""Tests for the `pytex-sandbox-init` console script.

The tests cover the checks that run first, the order of the steps, and the
mapping from a raw error to a helpful message.

No test starts Podman. The mocks replace the build, warm-up and check
helpers, so the tests see only the step order and the message text.
"""

from io import StringIO

import pytex_api.sandbox_init as init
from pytex_api.sandbox_init import (
    _friendly_error,
    _has_subid_range,
    _subid_configured,
    main,
)
from pytex_builder.console import Console


def _console() -> Console:
    return Console(StringIO())


def _text(console: Console) -> str:
    stream = console.stream
    assert isinstance(stream, StringIO)
    return stream.getvalue()


def _stub_steps(monkeypatch, *, podman=True, image_present=False, rootless=True):
    calls: dict[str, object] = {"build": [], "warm": 0}

    monkeypatch.setattr(init, "podman_available", lambda: podman)
    monkeypatch.setattr(init, "sandbox_image_present", lambda _image: image_present)
    monkeypatch.setattr(init, "_subid_configured", lambda: rootless)

    def _build(image):
        calls["build"].append(image)  # pyright: ignore[reportAttributeAccessIssue]

    def _warm(_config, **_kwargs):
        calls["warm"] += 1  # pyright: ignore[reportOperatorIssue]

    monkeypatch.setattr(init, "build_sandbox_image", _build)
    monkeypatch.setattr(init, "warm_sandbox_cache", _warm)
    return calls


# -- the check of the subuid and subgid ranges ------------------------------


def test_has_subid_range_matches_user_or_uid(tmp_path):
    f = tmp_path / "subuid"
    _ = f.write_text("alice:100000:65536\n", encoding="utf-8")
    assert _has_subid_range(f, {"alice"})
    assert _has_subid_range(f, {"1000", "alice"})
    assert not _has_subid_range(f, {"bob"})


def test_has_subid_range_missing_file_is_false(tmp_path):
    assert not _has_subid_range(tmp_path / "nope", {"alice"})


def test_subid_configured_true_when_no_user_keys(monkeypatch):
    # If PyTeX cannot identify the user, it skips the check. A skip prevents a
    # wrong report that the system is not configured.
    monkeypatch.setattr(init, "_current_user_keys", set)
    assert _subid_configured() is True


def test_subid_configured_requires_both_files(monkeypatch):
    monkeypatch.setattr(init, "_current_user_keys", lambda: {"alice"})
    # Only `/etc/subuid` holds a range. `/etc/subgid` holds none, so the
    # system is not configured.
    monkeypatch.setattr(
        init, "_has_subid_range", lambda path, _keys: "subuid" in str(path)
    )
    assert _subid_configured() is False


def test_subid_configured_true_when_both_present(monkeypatch):
    monkeypatch.setattr(init, "_current_user_keys", lambda: {"alice"})
    monkeypatch.setattr(init, "_has_subid_range", lambda _path, _keys: True)
    assert _subid_configured() is True


# -- the mapping from a raw error to a helpful message ----------------------


def test_friendly_error_subuid():
    msg = _friendly_error("newuidmap: write to uid_map failed: subuid range")
    assert "subuid/subgid" in msg
    assert "podman system migrate" in msg


def test_friendly_error_connection():
    msg = _friendly_error("Cannot connect to Podman socket")
    assert "podman info" in msg


def test_friendly_error_disk():
    assert "disk space" in _friendly_error("write error: no space left on device")


def test_friendly_error_falls_back_to_raw():
    assert _friendly_error("some novel failure") == "some novel failure"


# -- the step order of `main` -----------------------------------------------


def test_main_fails_without_podman(monkeypatch):
    calls = _stub_steps(monkeypatch, podman=False)
    console = _console()
    assert main([], console=console) == 1
    assert calls["build"] == []
    assert calls["warm"] == 0
    assert "podman is not installed" in _text(console)


def test_main_builds_and_warms(monkeypatch):
    calls = _stub_steps(monkeypatch, image_present=False)
    console = _console()
    assert main([], console=console) == 0
    assert len(calls["build"]) == 1  # pyright: ignore[reportArgumentType]
    assert calls["warm"] == 1
    assert "sandbox ready" in _text(console)


def test_main_skip_warm_builds_only(monkeypatch):
    calls = _stub_steps(monkeypatch)
    console = _console()
    assert main(["--skip-warm"], console=console) == 0
    assert len(calls["build"]) == 1  # pyright: ignore[reportArgumentType]
    assert calls["warm"] == 0
    assert "cache not warmed" in _text(console)


def test_main_skips_build_when_image_present(monkeypatch):
    calls = _stub_steps(monkeypatch, image_present=True)
    console = _console()
    assert main([], console=console) == 0
    assert calls["build"] == []  # the image is there and no flag forces a build
    assert calls["warm"] == 1
    assert "already present" in _text(console)


def test_main_force_build_rebuilds_present_image(monkeypatch):
    calls = _stub_steps(monkeypatch, image_present=True)
    assert main(["--force-build"], console=_console()) == 0
    assert len(calls["build"]) == 1  # pyright: ignore[reportArgumentType]


def test_main_uses_custom_image(monkeypatch):
    calls = _stub_steps(monkeypatch)
    assert main(["--image", "my/img:9"], console=_console()) == 0
    assert calls["build"] == ["my/img:9"]


def test_main_translates_build_failure(monkeypatch):
    _stub_steps(monkeypatch)

    def _boom(_image):
        raise RuntimeError("newuidmap failed: no subgid range")

    monkeypatch.setattr(init, "build_sandbox_image", _boom)
    console = _console()
    assert main([], console=console) == 1
    out = _text(console)
    assert "sandbox initialisation failed" in out
    assert "subuid/subgid" in out  # the script turns raw stderr into a hint


def test_main_warns_when_not_rootless(monkeypatch):
    _stub_steps(monkeypatch, rootless=False)
    console = _console()
    assert main([], console=console) == 0  # the script warns and continues
    assert "rootless podman may not be fully configured" in _text(console)
