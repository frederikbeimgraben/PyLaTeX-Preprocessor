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
    InputKind,
    OutputKind,
    TrustLevel,
    render_blob,
)
from pytex_api._sandbox import (
    CONTAINER_CACHE,
    CONTAINER_WORKDIR,
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


def test_memory_cap_present():
    cmd = _cmd(max_memory_bytes=123456)
    assert cmd[cmd.index("--memory") + 1] == "123456b"


def test_pids_and_cpu_caps_present():
    cmd = _cmd(config=SandboxConfig(mount_fonts=False, pids_limit=64, max_cpus="1.5"))
    assert cmd[cmd.index("--pids-limit") + 1] == "64"
    assert cmd[cmd.index("--cpus") + 1] == "1.5"


def test_tmpfs_scratch_is_mounted():
    assert any(arg.startswith("/tmp:rw") for arg in _cmd())


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
    assert f"{fonts}:{fonts}:ro" in cmd
    assert "/does/not/exist:/does/not/exist:ro" not in cmd


def test_image_then_inner_cmd_at_tail():
    cmd = _cmd(config=SandboxConfig(mount_fonts=False, image="example.test/img:1"))
    idx = cmd.index("example.test/img:1")
    assert cmd[idx + 1 :] == _INNER


def test_name_flag_added_when_given():
    cmd = _cmd(name="pytex-abc")
    assert cmd[cmd.index("--name") + 1] == "pytex-abc"


# -- live confined build (opt-in) ------------------------------------------


@pytest.mark.skipif(
    not (podman_available() and os.environ.get("PYTEX_TEST_PODMAN")),
    reason="set PYTEX_TEST_PODMAN=1 with podman installed to run the live build",
)
def test_untrusted_build_runs_through_podman_sandbox():
    # Warm-up (privileged): a TRUSTED build downloads tectonic + bundle so the
    # untrusted run can compile fully offline (--network none + --only-cached).
    # Generous timeouts: the first bundle fetch and the image pull can be slow.
    warm = render_blob(
        BuildRequest(
            source=b"# Warm\n\nWarm-up.",
            input_kind=InputKind.MARKDOWN,
            output_kind=OutputKind.PDF,
            trust=TrustLevel.TRUSTED,
            limits=BuildLimits(wall_timeout_s=600.0),
        )
    )
    assert warm.output[:5] == b"%PDF-"

    # The real test: untrusted input compiled inside the rootless sandbox.
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
