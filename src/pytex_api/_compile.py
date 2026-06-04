"""Confined tectonic compile: bytes of LaTeX -> bytes of PDF.

Everything runs inside the per-request workdir. For non-trusted builds the
subprocess is wrapped in POSIX resource limits, a wall-clock timeout, and a
fresh session/process-group so the whole tree can be killed; shell-escape is
forced off and ``--only-cached`` blocks any in-request network fetch.
"""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from ._models import CompileError, LimitError
from ._sandbox import (
    CONTAINER_BINARY,
    CONTAINER_WORKDIR,
    SandboxConfig,
    build_podman_cmd,
    podman_available,
    sandbox_image_present,
)
from ._security import (
    enforce_output_file_size,
    enforce_output_size,
    make_rlimit_preexec,
    truncate_log,
)

if TYPE_CHECKING:
    from pytex_builder.console import Console

    from ._models import BuildLimits, BuildRequest
    from ._policy import TrustPolicy

__all__ = ["compile_to_pdf"]

_JOB = "document"
_CONTAINER_BIN_NAME = "tectonic-bin"


def _locate_tectonic(policy: TrustPolicy, console: Console) -> Path:
    """Find a tectonic binary; download only if the policy allows network."""
    from pytex_builder.tectonic import CACHE_DIR, BuildError, ensure_tectonic

    on_path = shutil.which("tectonic")
    if on_path:
        return Path(on_path)
    cached = CACHE_DIR / "tectonic"
    if cached.exists():
        return cached
    if not policy.allow_network:
        raise CompileError(
            "tectonic is not installed and network is disabled for "
            + f"{policy.level.value} builds; pre-warm the binary out of band"
        )
    try:
        return ensure_tectonic(console)
    except BuildError as exc:
        raise CompileError(str(exc)) from exc


def build_tectonic_cmd(
    binary: Path,
    tex_file: Path,
    build_dir: Path,
    policy: TrustPolicy,
) -> list[str]:
    """Assemble the tectonic argv for ``policy`` (pure; unit-testable).

    Shell-escape is added only when the policy allows it; ``--only-cached`` is
    added whenever network is disabled, so a build can never trigger a bundle
    fetch.
    """
    cmd: list[str] = [
        str(binary),
        "--outdir",
        str(build_dir),
        "--keep-intermediates",
        "--keep-logs",
        "--synctex",
    ]
    if not policy.allow_network:
        cmd.append("--only-cached")
    if policy.allow_shell_escape:
        cmd += ["-Z", "shell-escape"]
        cmd += ["-Z", f"shell-escape-cwd={tex_file.parent.resolve()}"]
    cmd.append(str(tex_file))
    return cmd


def _kill_group(proc: subprocess.Popen[str]) -> None:  # pragma: no cover - timing
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except (ProcessLookupError, PermissionError, OSError):
        proc.kill()


def _run_confined(
    cmd: list[str],
    cwd: Path,
    limits: BuildLimits,
    *,
    apply_rlimits: bool,
) -> tuple[int, str]:
    """Run ``cmd`` with rlimits + a hard wall-clock kill; return (rc, output).

    ``apply_rlimits`` is the in-process ``setrlimit`` floor; it is switched off
    for the Podman path, where the container's cgroup flags do the capping (an
    rlimit on the ``podman`` *client* would not reach the build inside).
    """
    posix = os.name == "posix"
    preexec = make_rlimit_preexec(limits) if (apply_rlimits and posix) else None
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=posix,
            preexec_fn=preexec,
        )
    except OSError as exc:
        raise CompileError(f"could not start tectonic: {exc}") from exc

    try:
        out, _ = proc.communicate(timeout=limits.wall_timeout_s)
    except subprocess.TimeoutExpired:
        if posix:
            _kill_group(proc)
        else:  # pragma: no cover - non-POSIX fallback
            proc.kill()
        _ = proc.communicate()
        raise LimitError(
            f"compile exceeded the {limits.wall_timeout_s}s wall-clock limit"
        ) from None
    return proc.returncode, out or ""


def _should_sandbox(policy: TrustPolicy, config: SandboxConfig) -> bool:
    """Whether this build should run inside the Podman OS sandbox.

    Non-trusted builds (those that get rlimits) are sandboxed when ``podman`` is
    available and the pre-built image is already local - never pulling at
    request time. ``TRUSTED`` builds run un-containerised.
    """
    if not policy.apply_rlimits or not podman_available():
        return False
    return not config.tectonic_in_image or sandbox_image_present(config.image)


def _run_sandboxed(
    workdir: Path,
    build_dir: Path,
    req: BuildRequest,
    policy: TrustPolicy,
    config: SandboxConfig,
    console: Console,
) -> tuple[int, str]:
    """Build the ``podman run`` argv and run the compile confined.

    With ``tectonic_in_image`` the image's own ``tectonic`` is used; otherwise a
    located host binary is copied into the workdir (relabelled ``:Z``) and exec'd
    from there, never from a host system path.
    """
    if config.tectonic_in_image:
        container_binary = Path("tectonic")
    else:
        host_binary = _locate_tectonic(policy, console)
        container_bin = workdir / _CONTAINER_BIN_NAME
        _ = shutil.copy(host_binary, container_bin)
        container_bin.chmod(0o755)
        container_binary = Path(CONTAINER_BINARY)

    inner = build_tectonic_cmd(
        container_binary,
        Path(CONTAINER_WORKDIR) / f"{_JOB}.tex",
        Path(CONTAINER_WORKDIR) / build_dir.name,
        policy,
    )
    name = f"pytex-{workdir.name}"
    cmd = build_podman_cmd(
        workdir,
        inner,
        config,
        max_memory_bytes=req.limits.max_memory_bytes,
        max_fsize_bytes=req.limits.max_fsize_bytes,
        name=name,
    )
    try:
        return _run_confined(cmd, workdir, req.limits, apply_rlimits=False)
    except LimitError:
        # Wall-clock kill hit the podman client; force-remove the container so
        # the build inside cannot outlive the request.
        _ = subprocess.run(
            ["podman", "rm", "-f", name],
            capture_output=True,
            check=False,
        )
        raise


def compile_to_pdf(
    latex: str,
    req: BuildRequest,
    policy: TrustPolicy,
    workdir: Path,
    console: Console,
) -> tuple[bytes, str]:
    """Compile ``latex`` to PDF bytes inside ``workdir``; return (pdf, log).

    Caller-supplied ``assets`` (already name-validated) are written next to the
    ``.tex`` so ``\\includegraphics`` can resolve them. Non-trusted builds run
    inside a rootless Podman sandbox when ``podman`` is available; otherwise
    they fall back to the in-process ``setrlimit``/timeout floor (a warning is
    logged so the weaker confinement is never silent). The PDF is size-capped
    before it is read back.
    """
    tex_file = workdir / f"{_JOB}.tex"
    _ = tex_file.write_text(latex, encoding="utf-8")
    build_dir = workdir / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    for name, data in req.assets.items():
        _ = (workdir / name).write_bytes(data)

    config = SandboxConfig()
    if _should_sandbox(policy, config):
        rc, out = _run_sandboxed(workdir, build_dir, req, policy, config, console)
    elif policy.require_sandbox:
        # Fail closed: without the OS sandbox the in-process floor does NOT block
        # \input/\include/\openin of host files, so a downgrade would let
        # untrusted LaTeX read /etc/passwd into the PDF. Refuse instead.
        raise CompileError(
            f"the OS sandbox is required for {policy.level.value} PDF builds "
            + "but is unavailable (podman missing, or the image "
            + f"{config.image!r} is not pre-built); refusing to downgrade to "
            + "the weaker in-process confinement"
        )
    else:
        if policy.apply_rlimits:  # non-trusted, sandbox not required: warn loudly
            console.warn(
                "Podman sandbox unavailable (no podman, or image "
                + f"{config.image!r} not built); falling back to in-process "
                + "rlimits/timeout confinement, which does NOT block "
                + "\\input/\\openin of host files"
            )
        binary = _locate_tectonic(policy, console)
        cmd = build_tectonic_cmd(binary, tex_file, build_dir, policy)
        rc, out = _run_confined(
            cmd, workdir, req.limits, apply_rlimits=policy.apply_rlimits
        )

    log = truncate_log(out, req.limits)
    pdf = build_dir / f"{_JOB}.pdf"
    if rc != 0 or not pdf.exists():
        raise CompileError(
            f"tectonic failed to produce a PDF (exit {rc}).\n{log}".rstrip()
        )
    # Refuse a symlinked output before touching it: defense-in-depth against a
    # build that points document.pdf at a host file (not reachable today - no
    # shell-escape, \openout only writes regular files - but cheap to deny).
    if pdf.is_symlink():
        raise CompileError("refusing to read a symlinked output file")
    # Size-check via stat() *before* reading, so an oversize PDF never lands in
    # memory; the in-memory check then guards the bytes once read.
    enforce_output_file_size(pdf, req.limits)
    data = pdf.read_bytes()
    enforce_output_size(data, req.limits)
    return data, log
