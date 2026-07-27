"""Find, download and run the tectonic binary, biber and the makeindex step.

PyTeX downloads the tectonic binary once into a persistent user cache. The
cache is `$XDG_CACHE_HOME/pytex`, or `~/.cache/pytex`. The binary then survives
a reboot. A binary in `/tmp` does not. The official install script writes a
self-contained binary into its working directory, so PyTeX runs the script
inside the cache directory.
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
INSTALL_HINT = (
    "install tectonic manually and put it on PATH"
    " (see https://tectonic-typesetting.github.io/install.html)"
)


def _resolve_cache_dir() -> tuple[Path, str | None]:
    """Return the directory of the persistent binary cache.

    The function prefers `$XDG_CACHE_HOME/pytex`, then `~/.cache/pytex`. When
    neither resolves, it falls back to the system temp directory. `Path.home()`
    raises `RuntimeError` when `HOME` is unset, for example on a headless
    session or an RDP session. The fallback keeps the build alive, but the
    cache is no longer persistent.

    Returns:
        The cache directory and a warning text. The warning is `None` when the
        cache directory is persistent.
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

# BCF control-file format version -> the biber release that reads it.
# The pattern is: BCF minor = biber minor - 9. It holds for biber 2.14 and later.
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

# A mirror of the upstream biber binaries, hosted as release assets. SourceForge
# sometimes puts a download behind a Cloudflare challenge that curl cannot pass,
# so a build must not depend on it. PyTeX tries the mirror before SourceForge.
BIBER_MIRROR_URL = (
    "https://github.com/frederikbeimgraben/PyTeX-Preprocessor"
    "/releases/download/biber-binaries/{asset}"
)

# The SHA256 of each biber binary, keyed by the versioned mirror asset name.
# PyTeX checks a download from both sources against these values. The check also
# rejects an HTML error page that a CDN can serve with status 200. The table
# covers every mirrored platform: glibc and musl Linux x86_64, Linux aarch64,
# macOS x86_64 and universal, and Windows x86_64.
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
    """An external tool is missing, or it exited with a non-zero status."""


def _cached_binary() -> Path:
    return CACHE_DIR / "tectonic"


def ensure_tectonic(console: Console) -> Path:
    """Return the path to a usable tectonic binary.

    The function prefers a tectonic binary on `PATH`, then the cached one. When
    neither exists, it downloads tectonic into the cache.

    Raises:
        BuildError: `curl` or `sh` is missing, or the download failed.
    """
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


# On SourceForge the macOS binaries were under OSX_Intel up to biber 2.16. From
# 2.17 on they are under MacOS. The SourceForge fallback URL needs the right
# subdirectory for each version.
_OLD_MAC_DIRS: frozenset[str] = frozenset(
    {"2.11", "2.12", "2.13", "2.14", "2.15", "2.16"}
)


def _biber_candidates(version: str) -> list[tuple[str, str, str]]:
    """Return the biber download candidates for this platform, best first.

    Each candidate is the SourceForge subdirectory, the SourceForge file name,
    and the mirror asset name. The function returns more than one candidate
    where a fallback helps.

    * On Linux x86_64 the statically linked musl build comes first, because it
      needs no shared library. The glibc build needs `libnsl.so.1`, and many
      minimal systems do not have it. The glibc build is the fallback.
    * On macOS the universal build comes first. It is the only arm64-native
      option, and it exists from 2.17 on. The x86_64 build is the fallback, and
      it runs under Rosetta on Apple silicon.

    A candidate that upstream never published for a version returns 404, and
    the download loop then tries the next one.

    Raises:
        BuildError: PyTeX has no biber download for this platform.
    """
    system = platform.system()
    machine = platform.machine()
    mac_dir = "OSX_Intel" if version in _OLD_MAC_DIRS else "MacOS"
    # biber 2.19 renamed the musl tarball. Every other release uses the old name.
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
    """Report whether an archive member is the biber executable.

    Most archives hold a plain `biber`, or `biber.exe` on Windows. A few musl
    tarballs name the binary after the tarball, for example
    `biber-linux_x86_64-musl`. This function excludes an AppleDouble sidecar,
    whose name starts with `._`. The callers pick the largest matching member.
    """
    base = Path(name).name
    if base.startswith("._"):
        return False
    return base in {"biber", "biber.exe"} or base.startswith("biber")


def _extract_biber_binary(archive: Path, version: str) -> bytes:
    """Read the biber executable out of a `.tar.gz` or a `.zip` archive.

    Returns:
        The bytes of the executable.

    Raises:
        BuildError: The archive holds no biber executable, or the member cannot
            be read.
    """
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
    """Download `url` into `dest` and check the SHA256 of the result.

    Args:
        sha: The expected SHA256 hex digest. `None` skips the check.

    Returns:
        `True` when the download succeeded and the checksum matched. On a
        checksum mismatch the function deletes `dest` and returns `False`.
    """
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
    """Report whether `binary` runs on this host.

    The check runs `biber --version` and looks for exit status 0.

    PyTeX offers the musl build first, because it needs no glibc shared
    library. That build links dynamically against the musl loader. On a
    glibc-only host, for example Debian slim, it cannot exec at all and the
    kernel reports "No such file or directory". Running the binary is the only
    reliable check, so PyTeX runs it and falls back to the glibc build.
    """
    try:
        proc = subprocess.run(
            [str(binary), "--version"], capture_output=True, timeout=30
        )
    except OSError:
        return False
    return proc.returncode == 0


def _ensure_biber(version: str, console: Console) -> Path:
    """Return the path to biber `version`, downloading it when needed.

    PyTeX downloads each platform candidate in order, the musl build first and
    the glibc build second. It extracts the binary and runs it. It caches the
    first candidate that runs on this host. This keeps the choice correct on a
    host that lacks the musl loader or a glibc shared library.

    Raises:
        BuildError: `curl` is missing, or no candidate gave a working biber.
    """
    cached = _biber_cached(version)
    if cached.exists():
        # Check the cached binary again. An earlier release can have cached a
        # musl binary that cannot exec here, and PyTeX must replace it.
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
    """Return a biber that matches the BCF file of this build.

    The function reads the format version from `<build_dir>/<job>.bcf` and maps
    it through `BCF_TO_BIBER`. When the system biber already reports that
    version, the function returns it and downloads nothing.

    Returns:
        The path to a matching biber. The result is `None` when the BCF file is
        absent or unreadable, or when its format version is not in
        `BCF_TO_BIBER`.
    """
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
    # The system biber can already be the right version, so avoid a download.
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
    """Run tectonic with a no-op biber, so that it writes the BCF file.

    Tectonic deletes the intermediates when biber fails, so a real failed run
    never keeps the BCF file. A fake biber that exits 0 lets the TeX run finish
    and lets tectonic copy the BCF file into the build directory. This function
    suppresses the output, because the real compile pass follows at once.
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
    """Run one compile pass and keep the intermediates for the makeindex step.

    Raises:
        BuildError: tectonic exited with a non-zero status.
    """
    cmd: list[str] = [
        str(binary),
        "--outdir",
        str(build_dir),
        "--keep-intermediates",
        "--keep-logs",
        "--synctex",
    ]
    if shell_escape:
        # An inline image decodes its base64 data during the compile pass, so
        # it needs shell-escape and a stable working directory for it.
        cmd += ["-Z", "shell-escape"]
        cmd += ["-Z", f"shell-escape-cwd={tex_file.parent.resolve()}"]
    cmd.append(str(tex_file))

    job = tex_file.stem

    # The BCF file names the biber version this document needs. On the first
    # build, and after a clean, no BCF file exists yet. A silent probe pass with
    # a no-op biber makes tectonic write the BCF file into the build directory,
    # and it needs no installed biber.
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
    """Run the makeindex step for the `glossaries` package.

    A missing `makeindex` gives a warning, not a build failure.

    Returns:
        `True` when makeindex rebuilt at least one index. The document then
        needs one more compile pass.
    """
    makeindex = shutil.which("makeindex")
    style = build_dir / f"{job}.ist"

    # The (input, log, output) triples that the `glossaries` package produces.
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
