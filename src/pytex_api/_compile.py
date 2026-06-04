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
from typing import TYPE_CHECKING

from ._models import CompileError, LimitError
from ._security import enforce_output_size, make_rlimit_preexec, truncate_log

if TYPE_CHECKING:
    from pathlib import Path

    from pytex_builder.console import Console

    from ._models import BuildLimits, BuildRequest
    from ._policy import TrustPolicy

__all__ = ["compile_to_pdf"]

_JOB = "document"


def _locate_tectonic(policy: TrustPolicy, console: Console) -> Path:
    """Find a tectonic binary; download only if the policy allows network."""
    from pathlib import Path

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
    policy: TrustPolicy,
) -> tuple[int, str]:
    """Run ``cmd`` with rlimits + a hard wall-clock kill; return (rc, output)."""
    posix = os.name == "posix"
    preexec = make_rlimit_preexec(limits) if (policy.apply_rlimits and posix) else None
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


def compile_to_pdf(
    latex: str,
    req: BuildRequest,
    policy: TrustPolicy,
    workdir: Path,
    console: Console,
) -> tuple[bytes, str]:
    """Compile ``latex`` to PDF bytes inside ``workdir``; return (pdf, log).

    Caller-supplied ``assets`` (already name-validated) are written next to the
    ``.tex`` so ``\\includegraphics`` can resolve them. The PDF is size-capped
    before it is read back.
    """
    tex_file = workdir / f"{_JOB}.tex"
    _ = tex_file.write_text(latex, encoding="utf-8")
    build_dir = workdir / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    for name, data in req.assets.items():
        _ = (workdir / name).write_bytes(data)

    binary = _locate_tectonic(policy, console)
    cmd = build_tectonic_cmd(binary, tex_file, build_dir, policy)
    rc, out = _run_confined(cmd, workdir, req.limits, policy)

    log = truncate_log(out, req.limits)
    pdf = build_dir / f"{_JOB}.pdf"
    if rc != 0 or not pdf.exists():
        raise CompileError(
            f"tectonic failed to produce a PDF (exit {rc}).\n{log}".rstrip()
        )
    data = pdf.read_bytes()
    enforce_output_size(data, req.limits)
    return data, log
