"""Locate, download and drive the ``tectonic`` engine plus ``makeindex``.

The tectonic binary is fetched once into a persistent user cache
(``$XDG_CACHE_HOME/pytex`` or ``~/.cache/pytex``) so it survives a reboot
instead of being re-downloaded out of ``/tmp``. The official install script
drops a self-contained binary into its working directory - we point that at the
cache dir.
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
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING

__all__ = [
    "BuildError",
    "biber_for_build",
    "ensure_tectonic",
    "env_with_biber",
    "probe_bcf",
    "run_makeindex",
    "run_tectonic",
]

if TYPE_CHECKING:
    from .console import Console

INSTALL_URL = "https://drop-sh.fullyjustified.net"
# Where to put a manually-installed tectonic if the auto-download cannot run.
INSTALL_HINT = (
    "install tectonic manually and put it on PATH"
    " (see https://tectonic-typesetting.github.io/install.html)"
)


def _resolve_cache_dir() -> tuple[Path, str | None]:
    """Return ``(cache_dir, warning)`` for the persistent binary cache.

    Prefers ``$XDG_CACHE_HOME/pytex``, else ``~/.cache/pytex``. When neither is
    resolvable - e.g. ``HOME`` unset on a headless/RDP session, where
    ``Path.home()`` raises ``RuntimeError`` - it falls back to the system temp
    dir and returns a warning, so the cache degrades to non-persistent instead
    of crashing the build.
    """
    xdg = os.environ.get("XDG_CACHE_HOME")
    if xdg:
        return Path(xdg) / "pytex", None
    try:
        home = Path.home()
    except RuntimeError:
        fallback = Path(tempfile.gettempdir()) / "pytex-tectonic"
        return fallback, (
            "no home directory found (HOME unset?); caching tectonic/biber in "
            + f"{fallback}, which a reboot may clear. Set HOME or XDG_CACHE_HOME"
            + " for a persistent cache"
        )
    return home / ".cache" / "pytex", None


CACHE_DIR, _CACHE_WARNING = _resolve_cache_dir()

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

# SHA256 of each biber binary, keyed by the versioned mirror asset name. Used
# to verify downloads from either source and to reject HTML error pages a CDN
# might serve with a 200 status. Covers every mirrored platform (glibc/musl
# Linux x86_64, Linux aarch64, macOS x86_64/universal, Windows x86_64).
BIBER_SHA256: dict[str, str] = {
    "biber-2.11-darwin_x86_64.tar.gz": "4e3343574f917d7825148e4c9ccb665154476ec0817abf67f1fea052fb8cc728",
    "biber-2.11-linux_x86_64-musl.tar.gz": "a6b7e61446ee8b23cc0b6b1eaffd4a8e0d271f06874ad22b025cc41f74050617",
    "biber-2.11-linux_x86_64.tar.gz": "7fcb51491fb24151810a92b2e2d03b7a1291823c0f8d6fb53183af391fca42e7",
    "biber-2.11-MSWIN64.zip": "f3a438ae8d94e7afbd069f0f941b3d93816fc06647d88460ba05a5485ed4372a",
    "biber-2.12-darwin_x86_64.tar.gz": "5a5f20669bd3e4cf56fd246ef2ba37d601ca2059510590a5022da4487d5e7bb8",
    "biber-2.12-linux_x86_64.tar.gz": "fd0b5145cc908c400a701b583330635d533d750b73a272d1d5ea47e10b2fbf71",
    "biber-2.12-MSWIN64.zip": "96d99e075dbb666ad4ec93bcca5fcc15ea07b6f70e9151e7d44baa4cc7c02932",
    "biber-2.13-darwin_x86_64.tar.gz": "ad47307b6f27c7bb129a1a3235e01245be3e95541bba9adca6892196e599edfd",
    "biber-2.13-linux_x86_64-musl.tar.gz": "d4a25d32fef6993b5ea0dece70af4b09a1f2758f8b8737924250f3e6b80a979a",
    "biber-2.13-linux_x86_64.tar.gz": "03101f418d46f4666272b68a4318d9e4b7a840d9dfa05d93ddc490d491157a75",
    "biber-2.13-MSWIN64.zip": "bf3ab70629465d674d020a10f34e307c7f6fb031dc7ea73627a1fe53b1e8457b",
    "biber-2.14-darwin_x86_64.tar.gz": "d834ba71c05f8dfe668d4c40d13c0e11e0fee24e567877479a0ac1c98ad89131",
    "biber-2.14-linux_x86_64-musl.tar.gz": "0b6c2a8307111c6dc2897d338be1ad446ef2e1ca8d126f806ce5c9bf7ff486ca",
    "biber-2.14-linux_x86_64.tar.gz": "dab3177f03322b5529d07d47d21d9e573a90c23d86eaaf11591b2d155316ee1b",
    "biber-2.14-MSWIN64.zip": "247451621ef60378045cf917a007ef3219d3cbf833f080c3333927dea854b4fe",
    "biber-2.15-darwin_x86_64.tar.gz": "e2b4931db6b4a684b640f41e53faee1c68f931f03c41d8f2c40d8b11c85511c7",
    "biber-2.15-linux_x86_64-musl.tar.gz": "277acd35d51a07c1b75782514f88f1ad380581b0077548eaa0db6b60263dafaa",
    "biber-2.15-linux_x86_64.tar.gz": "653c8add18d2e94a233a6b9aae6d8144f965c2ce13fb7b4e66502b55fcd06e06",
    "biber-2.15-MSWIN64.zip": "61553ef3d5e8bdff86e1ac8204236fbf3980bc8ade94949f1ad874ba4031eb7f",
    "biber-2.16-darwin_x86_64.tar.gz": "c396133cc924c23111353ea5cb0e9960a98f1fddca8f42fbdb89e89424fc136f",
    "biber-2.16-linux_x86_64-musl.tar.gz": "e0935c8e67016889b3c8bb1f0fbd602b587f6935cd61ee23bc2eb898ae633f58",
    "biber-2.16-linux_x86_64.tar.gz": "3afb97a42d2cf272d3c0b51663725e55339c4e6f3d594cd52e16c39fa9fcfb13",
    "biber-2.16-MSWIN64.zip": "8e7a4c98626511bcf1c89a1847242cdd0e0113927137577eedaa13c72ce84b4b",
    "biber-2.17-darwin_universal.tar.gz": "182e1efa074d8a2a23a8893f2a22440d4e463cce55e4ed02076ac4c0ee0614b2",
    "biber-2.17-darwin_x86_64.tar.gz": "aa72ccdd01d59367b919d517f7a116e5dc40848abc1909cd812b485f791df7f4",
    "biber-2.17-linux_x86_64-musl.tar.gz": "8967c4d34bfd2ed3d71e54d8a20a0c766b90368348994c99fca56ee2d812619e",
    "biber-2.17-linux_x86_64.tar.gz": "129d2e0332a57e985ffa253e5e9fbd28ef99af5a068d1b141145211969aa8999",
    "biber-2.17-MSWIN64.zip": "c103bffc5ae0a7f513e7c26b6d394e9be6cf41952959c5d604ee2e6581b5dea2",
    "biber-2.18-darwin_universal.tar.gz": "a0848ca266334284f1145470e53c3882b2d5e8ad82828700df1f6e347f7b675b",
    "biber-2.18-darwin_x86_64.tar.gz": "f05520a397162434e93ef28b6be2c866f555a1979f150601fecf6d22d4bb8f2e",
    "biber-2.18-linux_x86_64-musl.tar.gz": "34da2cc489a1387bfda8c76add3d613ececd9b674d0361a2b1464cf592dee2ed",
    "biber-2.18-linux_x86_64.tar.gz": "2a6b4cd15a1139907799da0d23cd4ddcce8341af3960d2b3d1d3e4b4a9f1fb53",
    "biber-2.18-MSWIN64.zip": "02ee3a8b6838b7ff1e9aea1a5342686981b9364067a7b8e7131c3b3201cf387c",
    "biber-2.19-darwin_universal.tar.gz": "0ebda145064eb5b8901a4ed5c8c5e5e6a5208e0aba425f7febcb5fb5b1a9c11b",
    "biber-2.19-darwin_x86_64.tar.gz": "3835aab3247d3bff79b0c2fcf061149b80e39bf11f55a3a30cf946043a85d45b",
    "biber-2.19-linux_aarch64.tar.gz": "45571c262e714786ec841320ee1845f0e3e3cf29443bb58769b26c6fc6274766",
    "biber-2.19-linux_x86_64-musl.tar.gz": "66e765df8b52446659a978f35d25974b835b7168ddd96f45d4a49cea6bd727eb",
    "biber-2.19-linux_x86_64.tar.gz": "e2eda3e6ea7ac7e78d60e99a0e2aeb1096829f95791c06b768ed31a12889e58e",
    "biber-2.19-MSWIN64.zip": "f0bccdec320e89a04b067f1189957b4bbe6feb445005357601f6e295e83e97da",
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
            + " 'curl' and 'sh' on PATH;\n"
            + INSTALL_HINT
        )

    console.step("Downloading tectonic")
    console.detail(f"target: {cached}")
    if _CACHE_WARNING is not None:
        console.warn(_CACHE_WARNING)
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
            + "\n"
            + INSTALL_HINT
        )
    cached.chmod(0o755)
    return cached


# macOS binaries lived under OSX_Intel up to biber 2.16 and moved to MacOS
# from 2.17 on; the SourceForge fallback URL needs the right subdir per version.
_OLD_MAC_DIRS: frozenset[str] = frozenset(
    {"2.11", "2.12", "2.13", "2.14", "2.15", "2.16"}
)


def _biber_candidates(version: str) -> list[tuple[str, str, str]]:
    """``(sf_subdir, sf_filename, mirror_asset)`` for this platform, best first.

    More than one candidate is returned where a fallback helps:

    * Linux x86_64 prefers the statically-linked *musl* build, which has no
      shared-library dependencies (the glibc build needs e.g. ``libnsl.so.1``,
      absent on many minimal systems), then falls back to the glibc build.
    * macOS prefers the *universal* build (the only arm64-native option, added
      in 2.17), then the x86_64 build (runs under Rosetta on Apple silicon).

    Candidates upstream never published for a given version simply 404, and the
    download loop moves on to the next one.
    """
    system = platform.system()
    machine = platform.machine()
    mac_dir = "OSX_Intel" if version in _OLD_MAC_DIRS else "MacOS"
    # biber 2.19 renamed the musl tarball; earlier releases use the old name.
    musl_file = (
        "biber-linux-musl_x86_64.tar.gz"
        if version == "2.19"
        else "biber-linux_x86_64-musl.tar.gz"
    )
    if system == "Linux":
        if machine == "x86_64":
            return [
                ("Linux-musl", musl_file, f"biber-{version}-linux_x86_64-musl.tar.gz"),
                (
                    "Linux",
                    "biber-linux_x86_64.tar.gz",
                    f"biber-{version}-linux_x86_64.tar.gz",
                ),
            ]
        if machine in ("aarch64", "arm64"):
            return [
                (
                    "Linux",
                    "biber-linux_aarch64.tar.gz",
                    f"biber-{version}-linux_aarch64.tar.gz",
                ),
            ]
    elif system == "Darwin":
        return [
            (
                mac_dir,
                "biber-darwin_universal.tar.gz",
                f"biber-{version}-darwin_universal.tar.gz",
            ),
            (
                mac_dir,
                "biber-darwin_x86_64.tar.gz",
                f"biber-{version}-darwin_x86_64.tar.gz",
            ),
        ]
    elif system == "Windows":
        return [("Windows", "biber-MSWIN64.zip", f"biber-{version}-MSWIN64.zip")]
    raise BuildError(
        f"unsupported platform for biber auto-download: {system} {machine}"
    )


def _biber_cached(version: str) -> Path:
    name = "biber.exe" if platform.system() == "Windows" else "biber"
    return CACHE_DIR / "biber" / version / name


def _is_biber_member(name: str) -> bool:
    """Whether an archive member is the biber executable.

    Most archives hold a plain ``biber`` (``biber.exe`` on Windows), but a few
    musl tarballs name the binary after the tarball (e.g.
    ``biber-linux_x86_64-musl``). AppleDouble sidecars (``._biber``) are
    excluded. The largest matching member is chosen by the callers.
    """
    base = Path(name).name
    if base.startswith("._"):
        return False
    return base in {"biber", "biber.exe"} or base.startswith("biber")


def _extract_biber_binary(archive: Path, version: str) -> bytes:
    """Read the biber executable out of a ``.tar.gz`` or ``.zip`` archive."""
    if zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as zf:
            members = [
                i
                for i in zf.infolist()
                if not i.is_dir() and _is_biber_member(i.filename)
            ]
            if not members:
                raise BuildError(
                    f"biber binary not found inside the biber {version} archive"
                )
            return zf.read(max(members, key=lambda i: i.file_size))
    with tarfile.open(archive) as tf:
        tar_members = [
            m for m in tf.getmembers() if m.isfile() and _is_biber_member(m.name)
        ]
        member = max(tar_members, key=lambda m: m.size, default=None)
        if member is None:
            raise BuildError(
                f"biber binary not found inside the biber {version} archive"
            )
        src = tf.extractfile(member)
        if src is None:
            raise BuildError(f"could not read biber from the biber {version} archive")
        return src.read()


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


def _biber_runs(binary: Path) -> bool:
    """``True`` if ``binary`` actually executes here (``biber --version`` exits 0).

    The musl build is offered first (no glibc shared-lib deps) but is *dynamically*
    linked against the musl loader; on a glibc-only host (e.g. Debian-slim) it
    cannot exec at all ("No such file or directory"). Running it is the only
    reliable cross-check, so we verify and fall back to the glibc build."""
    try:
        proc = subprocess.run(
            [str(binary), "--version"], capture_output=True, timeout=30
        )
    except OSError:
        return False
    return proc.returncode == 0


def _ensure_biber(version: str, console: Console) -> Path:
    """Return a path to biber *version*, downloading from the mirror or SourceForge.

    Each platform candidate (musl first, then glibc) is downloaded, extracted and
    **test-run**; the first one that actually executes here is cached. This makes
    the choice robust on hosts that lack the musl loader or a glibc dependency."""
    cached = _biber_cached(version)
    if cached.exists():
        # Re-validate: a cache poisoned by an earlier release (e.g. a musl binary
        # that cannot exec here) must be replaced, not blindly reused.
        if _biber_runs(cached):
            return cached
        console.detail("cached biber does not execute here; re-downloading")
        cached.unlink(missing_ok=True)

    if not shutil.which("curl"):
        raise BuildError(
            "biber is not installed and cannot be downloaded without 'curl' on PATH"
        )

    console.step(f"Downloading biber {version}")
    cached.parent.mkdir(parents=True, exist_ok=True)
    tmp = cached.parent / "biber.download"
    cand = cached.parent / "biber.candidate"
    last: str | None = None
    try:
        for sf_dir, filename, asset in _biber_candidates(version):
            sha = BIBER_SHA256.get(asset)
            urls = [
                BIBER_MIRROR_URL.format(asset=asset),
                BIBER_RELEASE_URL.format(
                    version=version, sf_dir=sf_dir, filename=filename
                ),
            ]
            downloaded = False
            for url in urls:
                console.detail(f"source: {url}")
                if _download_to(url, tmp, sha, console):
                    downloaded = True
                    break
            if not downloaded:
                last = f"{asset}: download failed"
                continue
            try:
                cand.write_bytes(_extract_biber_binary(tmp, version))
                cand.chmod(0o755)
            except Exception as exc:
                last = f"{asset}: extract failed ({exc})"
                continue
            if _biber_runs(cand):
                cand.replace(cached)
                cached.chmod(0o755)
                return cached
            last = f"{asset}: does not execute on this platform"
            cand.unlink(missing_ok=True)
        raise BuildError(f"failed to obtain a working biber {version} ({last})")
    except Exception:
        if cached.exists():
            cached.unlink()
        raise
    finally:
        tmp.unlink(missing_ok=True)
        cand.unlink(missing_ok=True)


def biber_for_build(build_dir: Path, job: str, console: Console) -> Path | None:
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


def env_with_biber(biber: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["PATH"] = str(biber.parent) + os.pathsep + env.get("PATH", "")
    return env


def probe_bcf(cmd: list[str]) -> None:
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
        subprocess.run(cmd, env=env_with_biber(fake), capture_output=True)
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
    biber = biber_for_build(build_dir, job, console)
    if biber is None:
        probe_bcf(cmd)
        biber = biber_for_build(build_dir, job, console)

    env = env_with_biber(biber) if biber is not None else None
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
