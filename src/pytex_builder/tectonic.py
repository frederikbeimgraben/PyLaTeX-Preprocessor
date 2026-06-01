"""Locate, download and drive the ``tectonic`` engine plus ``makeindex``.

The tectonic binary is fetched once into a stable temp folder so repeated
builds reuse it. The official install script drops a self-contained binary into
its working directory - we point that at the cache dir.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from .console import Console

_INSTALL_URL = "https://drop-sh.fullyjustified.net"
_CACHE_DIR = Path(tempfile.gettempdir()) / "pytex-tectonic"


class BuildError(RuntimeError):
    """Raised when an external tool is missing or exits non-zero."""


def _cached_binary() -> Path:
    return _CACHE_DIR / "tectonic"


def ensure_tectonic(console: Console) -> Path:
    """Return a path to a usable ``tectonic`` binary, downloading if needed."""
    on_path = shutil.which("tectonic")
    if on_path:
        return Path(on_path)

    cached = _cached_binary()
    if cached.exists():
        return cached

    if not (shutil.which("curl") and shutil.which("sh")):
        raise BuildError(
            "tectonic is not installed and cannot be downloaded without"
            + " 'curl' and 'sh' on PATH"
        )

    console.step("Downloading tectonic")
    console.detail(f"target: {cached}")
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        f"curl --proto '=https' --tlsv1.2 -fsSL {_INSTALL_URL} | sh",
        shell=True,
        cwd=_CACHE_DIR,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0 or not cached.exists():
        raise BuildError(
            "failed to download tectonic:\n"
            + (proc.stderr.strip() or "no output from install script")
        )
    cached.chmod(0o755)
    return cached


def run_tectonic(
    binary: Path,
    tex_file: Path,
    build_dir: Path,
    *,
    shell_escape: bool,
) -> None:
    """Run a single tectonic pass, keeping intermediates for the glossary step."""
    cmd: list[str] = [
        str(binary),
        "--outdir",
        str(build_dir),
        "--keep-intermediates",
        "--keep-logs",
        "--synctex",
    ]
    if shell_escape:
        # shell-escape (and a stable cwd for it) is required so inline images
        # can decode their base64 payloads at compile time.
        cmd += ["-Z", "shell-escape"]
        cmd += ["-Z", f"shell-escape-cwd={tex_file.parent.resolve()}"]
    cmd.append(str(tex_file))

    proc = subprocess.run(cmd)
    if proc.returncode != 0:
        log = build_dir / f"{tex_file.stem}.log"
        raise BuildError(
            "tectonic failed to compile the document."
            + (f"\nSee the full log at {log}" if log.exists() else "")
        )


def run_makeindex(
    job: str,
    build_dir: Path,
    *,
    console: Console,
) -> bool:
    """Resolve glossary/acronym indices for ``glossaries``.

    Returns ``True`` if any index was (re)built, meaning a further tectonic
    pass is needed. Missing ``makeindex`` is a warning, not a fatal error.
    """
    makeindex = shutil.which("makeindex")
    style = build_dir / f"{job}.ist"

    # (input, log, output) triples produced by the glossaries package.
    targets = [
        (f"{job}.glo", f"{job}.glg", f"{job}.gls"),
        (f"{job}.acn", f"{job}.alg", f"{job}.acr"),
    ]
    present = [t for t in targets if (build_dir / t[0]).exists()]

    if not present or not style.exists():
        return False

    if not makeindex:
        console.warn("glossary entries found but 'makeindex' is not installed")
        console.hint(
            "install a TeX distribution providing 'makeindex'"
            + " (e.g. TeX Live) so glossaries and acronyms resolve"
        )
        return False

    console.step("Building glossaries")
    for source, log, output in present:
        proc = subprocess.run(
            [makeindex, "-s", style.name, "-t", log, "-o", output, source],
            cwd=build_dir,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            console.warn(f"makeindex failed for {source}")
            console.detail(proc.stderr.strip() or proc.stdout.strip())
            return False
        console.detail(f"{source} -> {output}")
    return True
