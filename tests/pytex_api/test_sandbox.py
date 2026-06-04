"""Podman sandbox wrapper: pure argv-flag assertions + an opt-in live build.

The flag tests mirror the ``--only-cached`` style from ``test_compile.py`` and
need no podman. The integration test is opt-in (``PYTEX_TEST_PODMAN=1`` and a
podman binary) because it pulls an image and pre-warms the tectonic bundle.
"""

import os
from pathlib import Path

import pytest

from pytex_api import (
    BuildLimits,
    BuildRequest,
    CompileError,
    InputKind,
    LimitError,
    OutputKind,
    TrustLevel,
    render_blob,
)
from pytex_api import _compile as compile_mod
from pytex_api._policy import policy_for
from pytex_api._sandbox import (
    CONTAINER_CACHE,
    CONTAINER_WORKDIR,
    MEMORY_FLOOR_BYTES,
    SandboxConfig,
    build_podman_cmd,
    podman_available,
)

_INNER = ["/work/tectonic-bin", "--outdir", "/work/build", "--only-cached", "doc.tex"]


def _cmd(**kw) -> list[str]:
    config = kw.pop("config", SandboxConfig(mount_fonts=False))
    return build_podman_cmd(
        Path("/tmp/work"),
        _INNER,
        config,
        max_memory_bytes=kw.pop("max_memory_bytes", 512 * 1024 * 1024),
        max_fsize_bytes=kw.pop("max_fsize_bytes", 256 * 1024 * 1024),
        **kw,
    )


# -- hardening flags -------------------------------------------------------


def test_network_is_disabled():
    cmd = _cmd()
    assert cmd[cmd.index("--network") + 1] == "none"


def test_rootfs_is_read_only():
    assert "--read-only" in _cmd()


def test_all_capabilities_dropped():
    cmd = _cmd()
    assert cmd[cmd.index("--cap-drop") + 1] == "ALL"


def test_no_new_privileges_set():
    cmd = _cmd()
    assert "no-new-privileges" in cmd


def test_default_seccomp_is_not_disabled():
    # No explicit profile -> podman's default applies; we must never weaken it.
    assert "seccomp=unconfined" not in _cmd()
    assert not any("seccomp" in arg for arg in _cmd())


def test_custom_seccomp_profile_is_passed():
    cmd = _cmd(config=SandboxConfig(mount_fonts=False, seccomp_profile=Path("/p.json")))
    assert "seccomp=/p.json" in cmd


# -- resource caps ---------------------------------------------------------


def test_memory_cap_present_above_floor():
    cmd = _cmd(max_memory_bytes=1024 * 1024 * 1024)
    assert cmd[cmd.index("--memory") + 1] == f"{1024 * 1024 * 1024}b"


def test_memory_floor_enforced_when_zero_or_negative():
    # A 0/negative limit must not drop --memory; it is floored, never absent.
    for bad in (0, -1):
        cmd = _cmd(max_memory_bytes=bad)
        assert "--memory" in cmd
        assert cmd[cmd.index("--memory") + 1] == f"{MEMORY_FLOOR_BYTES}b"


def test_memory_floor_does_not_lower_a_larger_limit():
    big = MEMORY_FLOOR_BYTES * 4
    cmd = _cmd(max_memory_bytes=big)
    assert cmd[cmd.index("--memory") + 1] == f"{big}b"


def test_pids_and_cpu_caps_present():
    cmd = _cmd(config=SandboxConfig(mount_fonts=False, pids_limit=64, max_cpus="1.5"))
    assert cmd[cmd.index("--pids-limit") + 1] == "64"
    assert cmd[cmd.index("--cpus") + 1] == "1.5"


def test_fsize_ulimit_present_above_floor():
    big = 100 * 1024 * 1024
    cmd = _cmd(max_fsize_bytes=big)
    assert cmd[cmd.index("--ulimit") + 1] == f"fsize={big}:{big}"


def test_fsize_floored_when_zero_or_negative():
    # Mirrors --memory: a 0/negative limit is floored, never dropped.
    from pytex_api._sandbox import FSIZE_FLOOR_BYTES

    for bad in (0, -1):
        cmd = _cmd(max_fsize_bytes=bad)
        assert cmd[cmd.index("--ulimit") + 1] == (
            f"fsize={FSIZE_FLOOR_BYTES}:{FSIZE_FLOOR_BYTES}"
        )


def test_tmpfs_scratch_is_mounted_noexec():
    tmpfs = next(arg for arg in _cmd() if arg.startswith("/tmp:rw"))
    assert "noexec" in tmpfs
    assert "nosuid" in tmpfs
    assert "nodev" in tmpfs


def test_xdg_cache_home_points_into_tmpfs():
    assert "XDG_CACHE_HOME=/tmp/.cache" in _cmd()


# -- mounts ----------------------------------------------------------------


def test_cache_mounted_as_ephemeral_overlay():
    cmd = _cmd(config=SandboxConfig(mount_fonts=False, cache_dir=Path("/host/cache")))
    assert f"/host/cache:{CONTAINER_CACHE}:O" in cmd


def test_workdir_is_the_only_rw_mount_and_relabelled():
    cmd = _cmd()
    assert f"/tmp/work:{CONTAINER_WORKDIR}:rw,Z" in cmd
    rw_mounts = [
        cmd[i + 1] for i, a in enumerate(cmd) if a == "-v" and ":rw" in cmd[i + 1]
    ]
    assert rw_mounts == [f"/tmp/work:{CONTAINER_WORKDIR}:rw,Z"]


def test_existing_font_dirs_mounted_read_only(tmp_path):
    fonts = tmp_path / "fonts"
    fonts.mkdir()
    cmd = _cmd(
        config=SandboxConfig(
            mount_fonts=True, font_dirs=(str(fonts), "/does/not/exist")
        )
    )
    # Plain :ro - NOT relabelled (:z of shared system dirs is rejected rootless;
    # see _existing_font_mounts). Missing dirs are skipped.
    assert f"{fonts}:{fonts}:ro" in cmd
    assert "/does/not/exist:/does/not/exist:ro" not in cmd


def test_image_then_inner_cmd_at_tail():
    cmd = _cmd(config=SandboxConfig(mount_fonts=False, image="example.test/img:1"))
    idx = cmd.index("example.test/img:1")
    assert cmd[idx + 1 :] == _INNER


def test_name_flag_added_when_given():
    cmd = _cmd(name="pytex-abc")
    assert cmd[cmd.index("--name") + 1] == "pytex-abc"


# -- _should_sandbox truth table (no podman needed; helpers mocked) --------


def _patch_podman(monkeypatch, *, available, image_present):
    monkeypatch.setattr(compile_mod, "podman_available", lambda: available)
    monkeypatch.setattr(
        compile_mod, "sandbox_image_present", lambda _image: image_present
    )


def test_should_sandbox_false_for_trusted(monkeypatch):
    _patch_podman(monkeypatch, available=True, image_present=True)
    assert not compile_mod._should_sandbox(
        policy_for(TrustLevel.TRUSTED), SandboxConfig()
    )


def test_should_sandbox_false_without_podman(monkeypatch):
    _patch_podman(monkeypatch, available=False, image_present=True)
    assert not compile_mod._should_sandbox(
        policy_for(TrustLevel.UNTRUSTED), SandboxConfig()
    )


def test_should_sandbox_false_when_image_missing(monkeypatch):
    _patch_podman(monkeypatch, available=True, image_present=False)
    assert not compile_mod._should_sandbox(
        policy_for(TrustLevel.UNTRUSTED), SandboxConfig()
    )


def test_should_sandbox_true_when_podman_and_image(monkeypatch):
    _patch_podman(monkeypatch, available=True, image_present=True)
    assert compile_mod._should_sandbox(
        policy_for(TrustLevel.UNTRUSTED), SandboxConfig()
    )


def test_should_sandbox_true_for_host_binary_without_image(monkeypatch):
    # tectonic_in_image=False mounts a host binary, so no image is needed.
    _patch_podman(monkeypatch, available=True, image_present=False)
    assert compile_mod._should_sandbox(
        policy_for(TrustLevel.UNTRUSTED),
        SandboxConfig(tectonic_in_image=False),
    )


# -- fail-closed (BLOCKER) -------------------------------------------------


@pytest.mark.parametrize("trust", [TrustLevel.UNTRUSTED, TrustLevel.SANDBOXED])
def test_pdf_build_fails_closed_without_sandbox(monkeypatch, trust):
    # No usable sandbox + require_sandbox -> refuse, never downgrade to the
    # in-process floor (which would not block \input of host files).
    _patch_podman(monkeypatch, available=False, image_present=False)
    with pytest.raises(CompileError, match="sandbox is required"):
        render_blob(
            BuildRequest(
                source=b"# Doc\n\nbody",
                input_kind=InputKind.MARKDOWN,
                output_kind=OutputKind.PDF,
                trust=trust,
            )
        )


def test_require_sandbox_set_for_non_trusted_only():
    assert policy_for(TrustLevel.UNTRUSTED).require_sandbox
    assert policy_for(TrustLevel.SANDBOXED).require_sandbox
    assert not policy_for(TrustLevel.TRUSTED).require_sandbox


# -- timeout cleanup: container force-removed ------------------------------


def test_timeout_force_removes_container(monkeypatch, tmp_path):
    build_dir = tmp_path / "build"
    build_dir.mkdir()

    def _boom(*_a, **_k):
        raise LimitError("timed out")

    removed: list[list[str]] = []

    def _record_run(cmd, *_a, **_k):
        removed.append(cmd)

        class _P:
            returncode = 0

        return _P()

    monkeypatch.setattr(compile_mod, "_run_confined", _boom)
    monkeypatch.setattr(compile_mod.subprocess, "run", _record_run)

    req = BuildRequest(
        source=b"x",
        input_kind=InputKind.TEX,
        output_kind=OutputKind.PDF,
        trust=TrustLevel.UNTRUSTED,
    )
    with pytest.raises(LimitError):
        compile_mod._run_sandboxed(
            tmp_path,
            build_dir,
            req,
            policy_for(TrustLevel.UNTRUSTED),
            SandboxConfig(),
            _Console(),
        )
    assert removed, "podman rm -f was not invoked on timeout"
    rm_cmd = removed[-1]
    assert rm_cmd[:3] == ["podman", "rm", "-f"]
    assert rm_cmd[3] == f"pytex-{tmp_path.name}"


# -- fallback warning when sandbox not required ----------------------------


class _Console:
    """Minimal console capturing warnings."""

    def __init__(self) -> None:
        self.warnings: list[str] = []

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def test_fallback_warns_when_sandbox_not_required(monkeypatch, tmp_path):
    import dataclasses

    _patch_podman(monkeypatch, available=False, image_present=False)
    # A non-trusted policy that explicitly does NOT require the sandbox.
    policy = dataclasses.replace(
        policy_for(TrustLevel.UNTRUSTED), require_sandbox=False
    )

    monkeypatch.setattr(compile_mod, "_locate_tectonic", lambda *_a: Path("tectonic"))

    def _fake_run(_cmd, cwd, _limits, *, apply_rlimits):
        # apply_rlimits stays on for the in-process floor.
        assert apply_rlimits is True
        (Path(cwd) / "build" / "document.pdf").write_bytes(b"%PDF-1.5\n")
        return 0, "ok"

    monkeypatch.setattr(compile_mod, "_run_confined", _fake_run)

    console = _Console()
    req = BuildRequest(
        source=rb"\section{x}",
        input_kind=InputKind.TEX,
        output_kind=OutputKind.PDF,
        trust=TrustLevel.UNTRUSTED,
    )
    pdf, _log = compile_mod.compile_to_pdf(
        rb"\section{x}".decode(), req, policy, tmp_path, console
    )
    assert pdf[:5] == b"%PDF-"
    assert any("falling back" in w for w in console.warnings)


# -- size cap before read (BLOCKER 2) --------------------------------------


def test_output_file_size_checked_before_read(tmp_path):
    from pytex_api._security import enforce_output_file_size

    big = tmp_path / "doc.pdf"
    _ = big.write_bytes(b"x" * 5000)
    with pytest.raises(LimitError, match="output file is"):
        enforce_output_file_size(big, BuildLimits(max_output_bytes=1000))


def test_symlinked_output_rejected(monkeypatch, tmp_path):
    # A build whose document.pdf is a symlink must be refused before any read.
    build_dir = tmp_path / "build"
    build_dir.mkdir()
    secret = tmp_path / "secret.bin"
    _ = secret.write_bytes(b"%PDF-host-secret")

    def _fake_run(_cmd, cwd, _limits, *, apply_rlimits):
        (Path(cwd) / "build" / "document.pdf").symlink_to(secret)
        return 0, "ok"

    _patch_podman(monkeypatch, available=False, image_present=False)
    monkeypatch.setattr(compile_mod, "_locate_tectonic", lambda *_a: Path("tectonic"))
    monkeypatch.setattr(compile_mod, "_run_confined", _fake_run)

    import dataclasses

    policy = dataclasses.replace(
        policy_for(TrustLevel.UNTRUSTED), require_sandbox=False
    )
    req = BuildRequest(
        source=rb"\section{x}",
        input_kind=InputKind.TEX,
        output_kind=OutputKind.PDF,
        trust=TrustLevel.UNTRUSTED,
    )
    with pytest.raises(CompileError, match="symlink"):
        compile_mod.compile_to_pdf(
            rb"\section{x}".decode(), req, policy, tmp_path, _Console()
        )


# -- live confined build (opt-in) ------------------------------------------


@pytest.mark.skipif(
    not (podman_available() and os.environ.get("PYTEX_TEST_PODMAN")),
    reason="set PYTEX_TEST_PODMAN=1 with podman installed to run the live build",
)
def test_untrusted_build_runs_through_podman_sandbox():
    from pytex_api._sandbox import (
        build_sandbox_image,
        sandbox_image_present,
        warm_sandbox_cache,
    )

    # Privileged warm-up (online, one-time): build the image and populate the
    # bundle cache with the IMAGE's own tectonic, so the offline untrusted run
    # gets a version-matched cache hit (--network none + --only-cached).
    if not sandbox_image_present():
        build_sandbox_image()
    warm_sandbox_cache()

    # The real test: untrusted input compiled fully offline inside the sandbox.
    res = render_blob(
        BuildRequest(
            source=b"# Sandboxed\n\nHello from inside Podman.",
            input_kind=InputKind.MARKDOWN,
            output_kind=OutputKind.PDF,
            trust=TrustLevel.UNTRUSTED,
            limits=BuildLimits(wall_timeout_s=300.0),
        )
    )
    assert res.output_kind is OutputKind.PDF
    assert res.output[:5] == b"%PDF-"
