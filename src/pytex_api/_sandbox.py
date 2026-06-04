"""Rootless Podman sandbox wrapper for untrusted / sandboxed compiles.

Wraps the tectonic argv in a ``podman run`` invocation that confines the build
to an ephemeral, network-less, read-only container:

* ``--network none`` - no network at all (the bundle is pre-warmed; untrusted
  builds also pass ``--only-cached`` so tectonic never tries to fetch),
* ``--read-only`` rootfs + a size-capped ``/tmp`` tmpfs for scratch,
* ``--cap-drop ALL`` + ``--security-opt no-new-privileges`` + Podman's default
  seccomp profile - trims the kernel attack surface,
* ``--memory`` / ``--pids-limit`` / ``--cpus`` - cgroups v2 resource caps,
* only the per-request workdir is mounted read-write (SELinux-relabelled with
  ``:Z``); the pre-warmed bundle cache is mounted as an ephemeral overlay
  (``:O``) so tectonic gets a writable view without ever mutating the host
  cache.

tectonic runs from the image itself (the image carries the binary + its shared
libs + fontconfig), so no host system path is exec-mounted. A statically-linked
host binary can instead be mounted by setting ``tectonic_in_image=False``.

This is defense-in-depth *on top of* the render-layer trust gating and the
``setrlimit``/timeout floor in :mod:`pytex_api._compile`. ``render_blob`` stays
sandbox-agnostic; the wrapper is selected by the :class:`TrustPolicy`.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from shutil import which

__all__ = [
    "CONTAINER_BINARY",
    "CONTAINER_CACHE",
    "CONTAINER_WORKDIR",
    "SandboxConfig",
    "build_podman_cmd",
    "build_sandbox_image",
    "podman_available",
    "sandbox_image_present",
]

# Container-internal mount points / paths.
CONTAINER_WORKDIR = "/work"
CONTAINER_BINARY = "/work/tectonic-bin"  # only used when a host binary is mounted
CONTAINER_CACHE = "/cache"
_CONTAINER_HOME = "/tmp"  # writable tmpfs; fontconfig / XDG scratch lands here

# Default image: a small Fedora base with tectonic (and its shared libs +
# fontconfig) installed from the distro repos. The build is a privileged
# warm-up step (see build_sandbox_image); an untrusted request never reaches
# the network. tectonic comes from the image so no host binary - which may be
# dynamically linked against libs the base image lacks - has to be smuggled in.
_DEFAULT_IMAGE = "localhost/pytex-tectonic:latest"
_BASE_IMAGE = "registry.fedoraproject.org/fedora-minimal:latest"
# tectonic is not a Fedora package, so install its official self-contained
# binary plus the shared libs it links (graphite2 + openssl; harfbuzz/freetype
# are statically bundled) and fontconfig for fontspec docs.
_CONTAINERFILE = (
    f"FROM {_BASE_IMAGE}\n"
    "RUN microdnf install -y graphite2 openssl-libs libstdc++ libgcc zlib "
    "fontconfig bash curl ca-certificates tar gzip && microdnf clean all\n"
    "RUN cd /tmp && curl --proto '=https' --tlsv1.2 -fsSL "
    "https://drop-sh.fullyjustified.net | sh "
    "&& install -m 0755 /tmp/tectonic /usr/local/bin/tectonic "
    "&& rm -f /tmp/tectonic\n"
)
_DEFAULT_PIDS_LIMIT = 256
_DEFAULT_MAX_CPUS = "2"
_DEFAULT_TMPFS_SIZE = "256m"

# Host font / fontconfig dirs, mounted read-only when present so fontspec docs
# can see system fonts. Basic (lmodern) builds need none of these - they come
# from the tectonic bundle.
_DEFAULT_FONT_DIRS: tuple[str, ...] = (
    "/usr/share/fonts",
    "/usr/local/share/fonts",
    "/usr/share/fontconfig",
    "/etc/fonts",
)


def _default_cache_dir() -> Path:
    """tectonic's bundle cache: ``$XDG_CACHE_HOME/Tectonic`` or ``~/.cache``."""
    xdg = os.environ.get("XDG_CACHE_HOME")
    base = Path(xdg) if xdg else Path.home() / ".cache"
    return base / "Tectonic"


@dataclass(frozen=True)
class SandboxConfig:
    """Knobs for the Podman sandbox; all have safe defaults."""

    image: str = _DEFAULT_IMAGE
    cache_dir: Path = field(default_factory=_default_cache_dir)
    font_dirs: tuple[str, ...] = _DEFAULT_FONT_DIRS
    pids_limit: int = _DEFAULT_PIDS_LIMIT
    max_cpus: str = _DEFAULT_MAX_CPUS
    tmpfs_size: str = _DEFAULT_TMPFS_SIZE
    # None -> Podman's built-in default seccomp profile (recommended). A path
    # points at a custom JSON profile passed via --security-opt seccomp=.
    seccomp_profile: Path | None = None
    # Mount existing host font dirs read-only into the container.
    mount_fonts: bool = True
    # True -> run the image's own ``tectonic`` (recommended; the image carries
    # the binary + its shared libs). False -> mount a host binary at
    # CONTAINER_BINARY (only safe with a statically-linked tectonic).
    tectonic_in_image: bool = True


def podman_available() -> bool:
    """Whether a ``podman`` binary is on PATH."""
    return which("podman") is not None


def sandbox_image_present(image: str = _DEFAULT_IMAGE) -> bool:
    """Whether ``image`` already exists locally (no network)."""
    if not podman_available():
        return False
    proc = subprocess.run(
        ["podman", "image", "exists", image],
        capture_output=True,
        check=False,
    )
    return proc.returncode == 0


def build_sandbox_image(
    image: str = _DEFAULT_IMAGE, *, timeout_s: float = 600.0
) -> None:
    """Build the tectonic sandbox image (privileged warm-up; needs network).

    Installs ``tectonic`` + ``fontconfig`` into a Fedora base. Run this once, out
    of band, never from an untrusted request path. Raises on failure.
    """
    # "-" reads the Containerfile from stdin with no build context (there is no
    # COPY/ADD), so the whole repo is not sent to the builder.
    proc = subprocess.run(
        ["podman", "build", "-t", image, "-"],
        input=_CONTAINERFILE,
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"failed to build sandbox image {image}:\n{proc.stderr.strip()}"
        )


def _existing_font_mounts(config: SandboxConfig) -> list[str]:
    mounts: list[str] = []
    if not config.mount_fonts:
        return mounts
    for src in config.font_dirs:
        if Path(src).is_dir():
            mounts += ["-v", f"{src}:{src}:ro"]
    return mounts


def build_podman_cmd(
    workdir: Path,
    inner_cmd: list[str],
    config: SandboxConfig,
    *,
    max_memory_bytes: int,
    name: str | None = None,
) -> list[str]:
    """Assemble the full ``podman run ...`` argv wrapping ``inner_cmd``.

    Pure and unit-testable. ``inner_cmd`` is the tectonic argv already expressed
    in *container* paths (binary at :data:`CONTAINER_BINARY`, files under
    :data:`CONTAINER_WORKDIR`); this function only prepends the container
    launcher, its hardening flags, and the mounts. ``name`` gives the container
    a stable name so it can be force-removed if the wall-clock kill fires.
    """
    cmd: list[str] = [
        "podman",
        "run",
        "--rm",
        "--network",
        "none",
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
    ]
    if name is not None:
        cmd += ["--name", name]
    if config.seccomp_profile is not None:
        cmd += ["--security-opt", f"seccomp={config.seccomp_profile}"]
    # else: Podman applies its default seccomp profile automatically.

    if max_memory_bytes > 0:
        cmd += ["--memory", f"{max_memory_bytes}b"]
    cmd += ["--pids-limit", str(config.pids_limit)]
    cmd += ["--cpus", config.max_cpus]
    cmd += ["--tmpfs", f"{_CONTAINER_HOME}:rw,nosuid,nodev,size={config.tmpfs_size}"]

    cmd += ["-e", f"HOME={_CONTAINER_HOME}"]
    cmd += ["-e", f"TECTONIC_CACHE_DIR={CONTAINER_CACHE}"]

    # Pre-warmed bundle cache as an ephemeral overlay: tectonic gets a writable
    # view, the host cache is never mutated, and Podman handles relabelling.
    cmd += ["-v", f"{config.cache_dir}:{CONTAINER_CACHE}:O"]
    cmd += _existing_font_mounts(config)
    # The only read-write mount: our private per-request workdir, SELinux
    # relabelled (:Z) so the container can read/write it under enforcing policy.
    cmd += ["-v", f"{workdir}:{CONTAINER_WORKDIR}:rw,Z"]
    cmd += ["--workdir", CONTAINER_WORKDIR]
    cmd.append(config.image)
    cmd += inner_cmd
    return cmd
