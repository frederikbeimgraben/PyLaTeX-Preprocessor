"""Locate, download and drive the ``tectonic`` engine plus ``makeindex``.

The tectonic binary is fetched once into a stable temp folder so repeated
builds reuse it. The official install script drops a self-contained binary into
its working directory - we point that at the cache dir.
"""

from __future__ import annotations

import hashlib
import os
import platform
import shutil
import subprocess
import tarfile
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import TYPE_CHECKING

__all__ = ["BuildError", "ensure_tectonic", "run_makeindex", "run_tectonic"]

if TYPE_CHECKING:
    from .console import Console

INSTALL_URL = "https://drop-sh.fullyjustified.net"
CACHE_DIR = Path(tempfile.gettempdir()) / "pytex-tectonic"

# BCF control-file format version -> compatible biber release.
# Pattern: BCF minor = biber minor - 9  (holds for biber 2.14+)
BCF_TO_BIBER: dict[str, str] = {
    "3.5": "2.14",
    "3.6": "2.15",
    "3.7": "2.16",
    "3.8": "2.17",
    "3.9": "2.18",
    "3.10": "2.19",
    "3.11": "2.20",
    "3.12": "2.21",
}

BIBER_RELEASE_URL = (
    "https://sourceforge.net/projects/biblatex-biber/files/"
    "biblatex-biber/{version}/binaries/{sf_dir}/{filename}/download"
)

# Mirror of the upstream biber binaries, hosted as release assets so builds
# survive SourceForge outages (it periodically gates downloads behind a
# Cloudflare challenge that curl cannot pass). Tried before SourceForge.
BIBER_MIRROR_URL = (
    "https://github.com/frederikbeimgraben/PyTeX-Preprocessor"
    "/releases/download/biber-binaries/{asset}"
)

# SHA256 of each upstream biber tarball, keyed by the versioned mirror asset
# name. Used to verify downloads from either source and to reject HTML error
# pages a CDN might serve with a 200 status. Linux x86_64 only for now; other
# platforms download from SourceForge without a pinned checksum.
BIBER_SHA256: dict[str, str] = {
    "biber-2.11-linux_x86_64.tar.gz": "7fcb51491fb24151810a92b2e2d03b7a1291823c0f8d6fb53183af391fca42e7",
    "biber-2.12-linux_x86_64.tar.gz": "fd0b5145cc908c400a701b583330635d533d750b73a272d1d5ea47e10b2fbf71",
    "biber-2.13-linux_x86_64.tar.gz": "03101f418d46f4666272b68a4318d9e4b7a840d9dfa05d93ddc490d491157a75",
    "biber-2.14-linux_x86_64.tar.gz": "dab3177f03322b5529d07d47d21d9e573a90c23d86eaaf11591b2d155316ee1b",
    "biber-2.15-linux_x86_64.tar.gz": "653c8add18d2e94a233a6b9aae6d8144f965c2ce13fb7b4e66502b55fcd06e06",
    "biber-2.16-linux_x86_64.tar.gz": "3afb97a42d2cf272d3c0b51663725e55339c4e6f3d594cd52e16c39fa9fcfb13",
    "biber-2.17-linux_x86_64.tar.gz": "129d2e0332a57e985ffa253e5e9fbd28ef99af5a068d1b141145211969aa8999",
    "biber-2.18-linux_x86_64.tar.gz": "2a6b4cd15a1139907799da0d23cd4ddcce8341af3960d2b3d1d3e4b4a9f1fb53",
    "biber-2.19-linux_x86_64.tar.gz": "e2eda3e6ea7ac7e78d60e99a0e2aeb1096829f95791c06b768ed31a12889e58e",
}


class BuildError(RuntimeError):
    """Raised when an external tool is missing or exits non-zero."""


def _cached_binary() -> Path:
    return CACHE_DIR / "tectonic"


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
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        f"curl --proto '=https' --tlsv1.2 -fsSL {INSTALL_URL} | sh",
        shell=True,
        cwd=CACHE_DIR,
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


def _biber_sf_path() -> tuple[str, str]:
    """Return (sourceforge_subdir, filename) for biber on this platform."""
    system = platform.system()
    machine = platform.machine()
    if system == "Linux":
        if machine == "x86_64":
            return "Linux", "biber-linux_x86_64.tar.gz"
        return "Linux-musl", f"biber-linuxmusl_{machine}.tar.gz"
    if system == "Darwin":
        arch = "arm64" if machine == "arm64" else "x86_64"
        return "MacOS", f"biber-darwin_{arch}.tar.gz"
    if system == "Windows":
        return "Windows", "biber-windows_x86_64.zip"
    raise BuildError(
        f"unsupported platform for biber auto-download: {system} {machine}"
    )


def _biber_cached(version: str) -> Path:
    return CACHE_DIR / "biber" / version / "biber"


def _mirror_asset(version: str, filename: str) -> str:
    """Versioned mirror asset name, e.g. ``biber-2.17-linux_x86_64.tar.gz``."""
    return filename.replace("biber-", f"biber-{version}-", 1)


def _biber_sources(version: str) -> list[tuple[str, str | None]]:
    """(url, expected_sha256 or None) pairs to try in order: mirror, then SourceForge."""
    sf_dir, filename = _biber_sf_path()
    asset = _mirror_asset(version, filename)
    sha = BIBER_SHA256.get(asset)
    return [
        (BIBER_MIRROR_URL.format(asset=asset), sha),
        (
            BIBER_RELEASE_URL.format(version=version, sf_dir=sf_dir, filename=filename),
            sha,
        ),
    ]


def _download_to(url: str, dest: Path, sha: str | None, console: Console) -> bool:
    """Fetch *url* into *dest*; return True only on success and matching checksum."""
    proc = subprocess.run(
        ["curl", "-fsSL", "-o", str(dest), url],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0 or not dest.exists():
        return False
    if sha is not None:
        actual = hashlib.sha256(dest.read_bytes()).hexdigest()
        if actual != sha:
            console.warn(f"checksum mismatch from {url}; discarding")
            dest.unlink(missing_ok=True)
            return False
    return True


def _ensure_biber(version: str, console: Console) -> Path:
    """Return a path to biber *version*, downloading from the mirror or SourceForge."""
    cached = _biber_cached(version)
    if cached.exists():
        return cached

    if not shutil.which("curl"):
        raise BuildError(
            "biber is not installed and cannot be downloaded without 'curl' on PATH"
        )

    console.step(f"Downloading biber {version}")
    cached.parent.mkdir(parents=True, exist_ok=True)
    tmp = cached.parent / "biber.download"
    try:
        downloaded = False
        for url, sha in _biber_sources(version):
            console.detail(f"source: {url}")
            if _download_to(url, tmp, sha, console):
                downloaded = True
                break
        if not downloaded:
            raise BuildError(
                f"failed to download biber {version} from the mirror or SourceForge"
            )
        with tarfile.open(tmp) as tf:
            member = next(
                (
                    m
                    for m in tf.getmembers()
                    if Path(m.name).name == "biber" and m.isfile()
                ),
                None,
            )
            if member is None:
                raise BuildError(
                    f"biber binary not found inside the biber {version} archive"
                )
            src = tf.extractfile(member)
            if src is None:
                raise BuildError(
                    f"could not read biber from the biber {version} archive"
                )
            cached.write_bytes(src.read())
    except Exception:
        if cached.exists():
            cached.unlink()
        raise
    finally:
        if tmp.exists():
            tmp.unlink()

    cached.chmod(0o755)
    return cached


def _biber_for_build(build_dir: Path, job: str, console: Console) -> Path | None:
    """Return a correctly-versioned biber if the BCF file reveals a mismatch."""
    bcf = build_dir / f"{job}.bcf"
    if not bcf.exists():
        return None
    try:
        root = ET.parse(bcf).getroot()
        bcf_ver = root.get("version")
    except ET.ParseError:
        return None
    if bcf_ver is None:
        return None
    biber_ver = BCF_TO_BIBER.get(bcf_ver)
    if biber_ver is None:
        console.warn(f"unknown BCF version {bcf_ver!r}; using system biber")
        return None
    # System biber may already be the right version - avoid downloading.
    system_biber = shutil.which("biber")
    if system_biber:
        result = subprocess.run(
            [system_biber, "--version"], capture_output=True, text=True
        )
        if f"biber version: {biber_ver}" in result.stdout:
            return Path(system_biber)
    return _ensure_biber(biber_ver, console)


def _env_with_biber(biber: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["PATH"] = str(biber.parent) + os.pathsep + env.get("PATH", "")
    return env


def _probe_bcf(cmd: list[str]) -> None:
    """Run tectonic with a no-op biber so the BCF file is written to build_dir.

    Tectonic cleans up intermediates when biber fails, so the BCF is never
    persisted on a real failed run. A fake biber that exits 0 lets the TeX
    pass finish and tectonic copy the BCF into ``build_dir``. Output is
    suppressed - the real pass immediately follows.
    """
    tmpdir = Path(tempfile.mkdtemp(prefix="pytex-fakeb-"))
    try:
        fake = tmpdir / "biber"
        fake.write_text("#!/bin/sh\nexit 0\n")
        fake.chmod(0o755)
        subprocess.run(cmd, env=_env_with_biber(fake), capture_output=True)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def run_tectonic(
    binary: Path,
    tex_file: Path,
    build_dir: Path,
    *,
    shell_escape: bool,
    console: Console,
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

    job = tex_file.stem

    # Determine the right biber from the BCF. If no BCF exists yet (first build
    # or after a clean), run a silent probe pass with a no-op biber so tectonic
    # writes the BCF to build_dir without actually needing biber installed.
    biber = _biber_for_build(build_dir, job, console)
    if biber is None:
        _probe_bcf(cmd)
        biber = _biber_for_build(build_dir, job, console)

    env = _env_with_biber(biber) if biber is not None else None
    proc = subprocess.run(cmd, env=env)
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
