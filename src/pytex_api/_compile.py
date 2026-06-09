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
    from collections.abc import Mapping

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


def _biber_env(
    cmd: list[str], build_dir: Path, policy: TrustPolicy, console: Console
) -> dict[str, str] | None:
    """A child env whose PATH includes the biber matching the document's BCF.

    Mirrors ``pytex_builder.tectonic.run_tectonic``: read the BCF (probing with a
    no-op biber if it is not written yet) to pick the right biber release, then
    ensure it (download+cache). Returns ``None`` (inherit env) for documents
    without biblatex, or when biber can't be obtained (e.g. network disabled) —
    tectonic then surfaces its own error rather than us masking it.
    """
    tex = build_dir.parent / f"{_JOB}.tex"
    try:
        source = tex.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    # No biblatex → tectonic never invokes biber; skip the extra probe pass.
    if "biblatex" not in source:
        return None
    try:
        from pytex_builder.tectonic import (  # pyright: ignore[reportPrivateUsage]
            _biber_for_build,
            _env_with_biber,
            _probe_bcf,
        )
    except Exception:  # pragma: no cover - import guard
        return None
    job = _JOB
    try:
        biber = _biber_for_build(build_dir, job, console)
        if biber is None and policy.allow_network:
            _probe_bcf(cmd)
            biber = _biber_for_build(build_dir, job, console)
    except Exception as exc:  # pragma: no cover - infra
        console.warn(f"biber setup skipped: {exc}")
        return None
    return _env_with_biber(biber) if biber is not None else None


def _run_confined(
    cmd: list[str],
    cwd: Path,
    limits: BuildLimits,
    *,
    apply_rlimits: bool,
    env: Mapping[str, str] | None = None,
) -> tuple[int, str]:
    """Run ``cmd`` with rlimits + a hard wall-clock kill; return (rc, output).

    ``apply_rlimits`` is the in-process ``setrlimit`` floor; it is switched off
    for the Podman path, where the container's cgroup flags do the capping (an
    rlimit on the ``podman`` *client* would not reach the build inside).
    ``env`` overrides the child environment (e.g. a PATH that includes biber).
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
            env=dict(env) if env is not None else None,
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
    assets: Mapping[str, bytes],
) -> tuple[bytes, str]:
    """Compile ``latex`` to PDF bytes inside ``workdir``; return (pdf, log).

    ``assets`` is the *name-validated* mapping from :func:`filter_assets`; it is
    written next to the ``.tex`` so ``\\includegraphics`` can resolve it. Writing
    this checked dict - rather than re-iterating ``req.assets`` - keeps the
    workdir-escape guarantee independent of call order. Non-trusted builds run
    inside a rootless Podman sandbox when ``podman`` is available; otherwise
    they fall back to the in-process ``setrlimit``/timeout floor (a warning is
    logged so the weaker confinement is never silent). The PDF is size-capped
    before it is read back.
    """
    tex_file = workdir / f"{_JOB}.tex"
    _ = tex_file.write_text(latex, encoding="utf-8")
    build_dir = workdir / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    for name, data in assets.items():
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
        # biblatex docs (report/protocol) make tectonic shell out to ``biber``;
        # it is not bundled, so provide a version-matched one on PATH (probe the
        # BCF, then download+cache the matching biber). Without it tectonic dies
        # with "Running external tool biber ... No such file or directory".
        biber_env = _biber_env(cmd, build_dir, policy, console)
        rc, out = _run_confined(
            cmd,
            workdir,
            req.limits,
            apply_rlimits=policy.apply_rlimits,
            env=biber_env,
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
