"""Confined tectonic compile: LaTeX text -> PDF bytes.

Every step runs inside the temporary work directory of the request. For a
non-trusted build, PyTeX wraps the subprocess in POSIX resource limits, a
wall-clock timeout, and a new session and process group. The new process group
lets PyTeX kill the whole process tree. PyTeX also forces shell-escape off, and
`--only-cached` blocks every network fetch during the request.
"""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from ._models import CompileError, LimitError, TrustError
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
    """Find the tectonic binary, and download it only if the policy allows it.

    Returns:
        The path to the tectonic binary, from PATH or from the cache.

    Raises:
        CompileError: tectonic is not installed and the policy blocks the
            network, or the download failed.
    """
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
    """Assemble the tectonic argv for `policy`.

    The function is pure, so a unit test can call it directly. PyTeX adds
    shell-escape only when the policy allows it. PyTeX adds `--only-cached`
    whenever the policy blocks the network, so a build can never start a
    bundle fetch.

    Returns:
        The tectonic argv, with the input file as the last item.
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
    """Build a child environment whose PATH holds the biber for this document.

    This mirrors `pytex_builder.tectonic.run_tectonic`. PyTeX reads the BCF
    file to pick the correct biber release, and then downloads and caches that
    release. If tectonic has not written the BCF file yet, PyTeX first runs a
    probe compile pass with a no-op biber.

    Returns:
        A full environment mapping for the child process, or `None` when the
        caller must inherit the current environment. The result is `None` for
        a document without biblatex, and when PyTeX cannot get biber, for
        example because the policy blocks the network. tectonic then reports
        its own error instead of a masked one.
    """
    tex = build_dir.parent / f"{_JOB}.tex"
    try:
        source = tex.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    # Without biblatex, tectonic never calls biber. Skip the extra probe pass.
    if "biblatex" not in source:
        return None
    try:
        from pytex_builder.tectonic import biber_for_build, env_with_biber, probe_bcf
    except Exception:  # pragma: no cover - import guard
        return None
    job = _JOB
    try:
        biber = biber_for_build(build_dir, job, console)
        if biber is None and policy.allow_network:
            probe_bcf(cmd)
            biber = biber_for_build(build_dir, job, console)
    except Exception as exc:  # pragma: no cover - infra
        console.warn(f"biber setup skipped: {exc}")
        return None
    return env_with_biber(biber) if biber is not None else None


def _run_confined(
    cmd: list[str],
    cwd: Path,
    limits: BuildLimits,
    *,
    apply_rlimits: bool,
    env: Mapping[str, str] | None = None,
) -> tuple[int, str]:
    """Run `cmd` with resource limits and a hard wall-clock kill.

    Args:
        apply_rlimits: Turn on the in-process `setrlimit` floor. The Podman
            path passes `False`, because the cgroup flags of the container do
            the capping there. An rlimit on the `podman` client process would
            not reach the build inside the container.
        env: A full replacement for the child environment, for example a PATH
            that holds biber. `None` inherits the environment of this process.

    Returns:
        The exit code of the process, and its stdout with stderr merged in.

    Raises:
        CompileError: The process could not start.
        LimitError: The process passed the wall-clock limit.
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
    """Report whether this build runs inside the Podman sandbox.

    A non-trusted build is a build that gets rlimits. Such a build uses the
    sandbox when `podman` is on PATH. When `config.tectonic_in_image` is true,
    the pre-built image must also be local already, because PyTeX must never
    pull an image at request time. When `config.tectonic_in_image` is false,
    this function reports true without any image check. A `trusted` build runs
    without a container.
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
    """Build the `podman run` argv and run the compile confined.

    With `config.tectonic_in_image` the build uses the tectonic binary of the
    image. If not, PyTeX copies a host binary into the temporary work
    directory and runs the copy from there. Podman relabels that directory
    with `:Z`. PyTeX never runs a binary from a host system path.

    Returns:
        The exit code of `podman run`, and its stdout with stderr merged in.
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
        # The wall-clock kill hit the podman client. Force-remove the
        # container, so the build inside cannot outlive the request.
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
    """Compile `latex` to PDF bytes inside `workdir`.

    A non-trusted build runs inside a rootless Podman sandbox when `podman` is
    available. If the policy demands the sandbox and the sandbox is missing,
    this function fails closed. If the policy does not demand the sandbox, the
    build falls back to the in-process `setrlimit` and timeout floor. PyTeX
    then logs a warning, so the weaker confinement is never silent. PyTeX
    checks the PDF size before it reads the file.

    Args:
        assets: The name-validated mapping from `filter_assets`. PyTeX writes
            these files next to the rendered `.tex` file, so
            `\\includegraphics` can find them. PyTeX writes this checked dict
            and never reads `req.assets` again, so the workdir-escape
            guarantee does not depend on the call order.

    Returns:
        The PDF bytes, and the compile log truncated to the log limit.

    Raises:
        CompileError: The policy demands the Podman sandbox and the sandbox is
            not available. This error also covers a non-zero tectonic exit, a
            missing PDF, and a PDF that is a symbolic link.
        LimitError: The compile passed the wall-clock limit, or the PDF is
            larger than `req.limits.max_output_bytes`.
    """
    tex_file = workdir / f"{_JOB}.tex"
    _ = tex_file.write_text(latex, encoding="utf-8")
    build_dir = workdir / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    for name, data in assets.items():
        # `document.tex` is the file PyTeX just wrote from the rendered,
        # allowlist-screened LaTeX. An asset of that name must not land here,
        # or it silently replaces the screened file with unscanned content.
        if name == tex_file.name:
            raise TrustError(
                f"asset name {name!r} would overwrite the rendered, "
                + "package-screened LaTeX file; rename the asset"
            )
        _ = (workdir / name).write_bytes(data)

    config = SandboxConfig()
    if _should_sandbox(policy, config):
        rc, out = _run_sandboxed(workdir, build_dir, req, policy, config, console)
    elif policy.require_sandbox:
        # Fail closed. Without the Podman sandbox, the in-process floor does
        # not block `\input`, `\include`, or `\openin` of host files. A
        # downgrade would let untrusted LaTeX read /etc/passwd into the PDF.
        raise CompileError(
            f"the OS sandbox is required for {policy.level.value} PDF builds "
            + "but is unavailable (podman missing, or the image "
            + f"{config.image!r} is not pre-built); refusing to downgrade to "
            + "the weaker in-process confinement"
        )
    else:
        if policy.apply_rlimits:  # non-trusted, and the sandbox is optional
            console.warn(
                "Podman sandbox unavailable (no podman, or image "
                + f"{config.image!r} not built); falling back to in-process "
                + "rlimits/timeout confinement, which does NOT block "
                + "\\input/\\openin of host files"
            )
        binary = _locate_tectonic(policy, console)
        cmd = build_tectonic_cmd(binary, tex_file, build_dir, policy)
        # A biblatex document (a report or a meeting protocol) makes tectonic
        # call `biber`. tectonic does not bundle biber, so put a
        # version-matched biber on PATH. PyTeX probes the BCF file, then
        # downloads and caches the matching biber. Without it, tectonic stops
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
    # Refuse a symbolic link before PyTeX reads the file. This is
    # defense-in-depth against a build that points document.pdf at a host
    # file. No build can do that today, because shell-escape is off and
    # `\openout` writes only regular files, but the check is cheap.
    if pdf.is_symlink():
        raise CompileError("refusing to read a symlinked output file")
    # Check the size with stat() before the read, so an oversize PDF never
    # lands in memory. The in-memory check then guards the bytes once read.
    enforce_output_file_size(pdf, req.limits)
    data = pdf.read_bytes()
    enforce_output_size(data, req.limits)
    return data, log
