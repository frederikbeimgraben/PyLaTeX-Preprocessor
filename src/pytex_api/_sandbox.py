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
import platform
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from shutil import rmtree, which

__all__ = [
    "CONTAINER_BINARY",
    "CONTAINER_CACHE",
    "CONTAINER_WORKDIR",
    "MEMORY_FLOOR_BYTES",
    "SandboxConfig",
    "build_podman_cmd",
    "build_sandbox_image",
    "podman_available",
    "sandbox_image_present",
    "warm_sandbox_cache",
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
# Base pinned by digest (not a moving :latest tag) for a reproducible,
# supply-chain-auditable build.
_BASE_IMAGE = (
    "registry.fedoraproject.org/fedora-minimal"
    "@sha256:7d847227f0f90b4d45566c9a2ba67b5d36a286b798dbdf27f24d2c02a23b6489"
)
# tectonic is not a Fedora package, so install a pinned upstream release and
# verify its sha256 (instead of piping the latest installer to a shell). The
# shared libs it links (graphite2 + openssl; harfbuzz/freetype are statically
# bundled) and fontconfig (for fontspec docs) come from the distro.
_TECTONIC_VERSION = "0.16.9"
# Per-arch upstream release asset + its sha256. The image is built natively on
# the host, so the asset must match the build host's CPU arch: x86_64 uses the
# glibc build (its shared libs come from the distro install line below);
# aarch64 ships only a statically-linked musl build upstream. A hard-coded
# x86_64 asset produced an "exec format error" when the image was built on ARM.
_TECTONIC_ASSETS: dict[str, tuple[str, str]] = {
    "x86_64": (
        "x86_64-unknown-linux-gnu",
        "f3c825128095dc3399ea11c08c18035b33050a216930c295c79e8eb11bd21de4",
    ),
    "aarch64": (
        "aarch64-unknown-linux-musl",
        "f9aa39017dbd51f111fdb93dda222178cbe51c8193508fc567b523cc74fff9c1",
    ),
}
# platform.machine() spelling -> a key in _TECTONIC_ASSETS.
_ARCH_ALIASES: dict[str, str] = {
    "x86_64": "x86_64",
    "amd64": "x86_64",
    "aarch64": "aarch64",
    "arm64": "aarch64",
}


def _tectonic_url(target: str) -> str:
    """The upstream release URL for a ``<arch>-<vendor>-<os>-<abi>`` *target*."""
    return (
        "https://github.com/tectonic-typesetting/tectonic/releases/download/"
        f"tectonic%40{_TECTONIC_VERSION}/"
        f"tectonic-{_TECTONIC_VERSION}-{target}.tar.gz"
    )


def _containerfile(machine: str | None = None) -> str:
    """Render the sandbox Containerfile for *machine* (default: host arch).

    The tectonic download URL + sha256 are chosen by architecture so the image
    builds correctly on both x86_64 and aarch64 hosts. The musl aarch64 binary
    is static, so the extra ``graphite2``/``openssl-libs`` packages it does not
    link are harmless there; ``fontconfig`` is needed by both for fontspec.
    """
    raw = (machine or platform.machine()).lower()
    arch = _ARCH_ALIASES.get(raw)
    if arch is None:
        supported = ", ".join(sorted(set(_ARCH_ALIASES.values())))
        raise RuntimeError(
            f"unsupported architecture for the tectonic sandbox image: {raw!r}"
            + f" (supported: {supported})"
        )
    target, sha = _TECTONIC_ASSETS[arch]
    url = _tectonic_url(target)
    return (
        f"FROM {_BASE_IMAGE}\n"
        "RUN microdnf install -y graphite2 openssl-libs libstdc++ libgcc zlib "
        "fontconfig curl ca-certificates tar gzip && microdnf clean all\n"
        f"RUN cd /tmp && curl --proto '=https' --tlsv1.2 -fsSL -o tectonic.tar.gz "
        f"'{url}' "
        f'&& echo "{sha}  tectonic.tar.gz" | sha256sum -c - '
        "&& tar xzf tectonic.tar.gz "
        "&& install -m 0755 tectonic /usr/local/bin/tectonic "
        "&& rm -f tectonic tectonic.tar.gz\n"
    )


_DEFAULT_PIDS_LIMIT = 256
_DEFAULT_MAX_CPUS = "2"
_DEFAULT_TMPFS_SIZE = "256m"
# Floors enforced for non-trusted builds so a 0/negative limit cannot drop a
# cap entirely (an unbounded container is a host OOM/disk-DoS vector).
MEMORY_FLOOR_BYTES = 256 * 1024 * 1024
FSIZE_FLOOR_BYTES = 64 * 1024 * 1024

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

    Installs ``tectonic`` + ``fontconfig`` into a Fedora base, selecting the
    tectonic binary for the build host's CPU architecture. Run this once, out
    of band, never from an untrusted request path. Raises on failure.
    """
    # "-" reads the Containerfile from stdin with no build context (there is no
    # COPY/ADD), so the whole repo is not sent to the builder.
    proc = subprocess.run(
        ["podman", "build", "-t", image, "-"],
        input=_containerfile(),
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"failed to build sandbox image {image}:\n{proc.stderr.strip()}"
        )


# Representative warm-up documents: one per offline-relevant variant, each
# carrying that variant's *real* preamble (HSRT report fonts, protocol header
# packages). Warming with these - rather than a bare "# Warm" stub - pulls the
# exact bundle resources the offline (--network none + --only-cached) builds
# need, so a real report or protocol does not cache-miss on its first compile.
_WARM_SAMPLES: tuple[tuple[str | None, bytes], ...] = (
    (None, b"# Warm\n\nWarm-up body.\n"),
    ("report", b"---\ntitle: Warm Report\nauthor: PyTeX\n---\n# Intro\n\nBody.\n"),
    (
        "protocol-asta",
        b"---\ngremium: AStA\ndatum: 2026-01-01\nanwesend: [A, B]\n---\n"
        + b"# TOP 1\n\n> [!beschluss] Beschluss\n> Warm-up decision.\n",
    ),
    (
        "protocol-stupa",
        b"---\ngremium: StuPa\ndatum: 2026-01-01\nanwesend: [A, B]\n---\n"
        + b"# TOP 1\n\n> [!abstimmung] Abstimmung\n> Warm-up vote.\n",
    ),
)


def _write_warm_documents(work: Path) -> list[str]:
    """Render each warm sample to LaTeX in *work*; return the ``.tex`` names.

    Renders through the TRUSTED policy so the variant preambles come out exactly
    as a real build would emit them. Pure rendering - no network, no container.
    """
    from ._models import BuildRequest, InputKind, TrustLevel
    from ._policy import policy_for
    from ._render import render_to_latex

    policy = policy_for(TrustLevel.TRUSTED)
    rendered = [
        (
            f"warm-{index}.tex",
            render_to_latex(
                BuildRequest(
                    source=source,
                    input_kind=InputKind.MARKDOWN,
                    trust=TrustLevel.TRUSTED,
                    variant=variant,
                ),
                policy,
                work,
            ),
        )
        for index, (variant, source) in enumerate(_WARM_SAMPLES)
    ]
    for name, latex in rendered:
        _ = (work / name).write_text(latex, encoding="utf-8")
    return [name for name, _ in rendered]


def _warm_podman_cmd(config: SandboxConfig, work: Path, tex_name: str) -> list[str]:
    """``podman run`` argv that warms the cache from *tex_name* (pure; testable).

    Network ON (default), cache mounted read-write with a *shared* (:z) relabel
    - NOT private (:Z). The cache is the shared lower layer that later request
    containers read via :O and that the host-side TRUSTED build reads directly;
    a private MCS category (:Z) would deny those readers under enforcing
    SELinux. :z is allowed here because the cache lives in the user's $HOME (he
    owns it), unlike shared system dirs.
    """
    return [
        "podman",
        "run",
        "--rm",
        # Host netns for the one-time privileged warm-up so the bundle can be
        # fetched even where rootless slirp/pasta networking is unavailable.
        # This is NOT the untrusted path (which always runs --network none).
        "--network",
        "host",
        "-v",
        f"{config.cache_dir}:{CONTAINER_CACHE}:z",
        "-v",
        f"{work}:{CONTAINER_WORKDIR}:rw,Z",
        "--workdir",
        CONTAINER_WORKDIR,
        "--tmpfs",
        f"{_CONTAINER_HOME}:rw",
        "-e",
        f"HOME={_CONTAINER_HOME}",
        "-e",
        f"TECTONIC_CACHE_DIR={CONTAINER_CACHE}",
        config.image,
        "tectonic",
        "--outdir",
        CONTAINER_WORKDIR,
        tex_name,
    ]


def warm_sandbox_cache(
    config: SandboxConfig | None = None, *, timeout_s: float = 600.0
) -> None:
    """Populate the bundle cache using the *image's own* tectonic (one-time).

    A privileged warm-up: runs the sandbox image online with the cache mounted
    read-write so the fetched bundle is written to the host cache by the exact
    tectonic version that the confined builds use. One compile per representative
    variant (plain, report, protocol-*) so the offline (``--network none`` +
    ``--only-cached``) request does not cache-miss on a real document's preamble.
    Without this, a cache warmed by a differently-versioned host tectonic - or by
    a minimal stub missing the report/protocol fonts - can miss, and the offline
    request would then fail. Never call from an untrusted request path. Raises on
    failure.
    """
    cfg = config or SandboxConfig()
    cfg.cache_dir.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="pytex-warm-"))
    try:
        for tex_name in _write_warm_documents(work):
            proc = subprocess.run(
                _warm_podman_cmd(cfg, work, tex_name),
                capture_output=True,
                text=True,
                timeout=timeout_s,
                check=False,
            )
            if proc.returncode != 0:
                raise RuntimeError(
                    f"failed to warm sandbox cache for {tex_name}:\n"
                    + proc.stderr.strip()
                )
    finally:
        rmtree(work, ignore_errors=True)


def _existing_font_mounts(config: SandboxConfig) -> list[str]:
    """Read-only mounts of host font dirs that exist.

    SELinux caveat: these are mounted plain ``:ro``, *not* relabelled. A ``:z``
    relabel of shared system dirs (``/usr/share/fonts`` ...) is rejected rootless
    (``lsetxattr ... operation not permitted`` - the user does not own those
    files), so relabelling is not an option here. Under strict enforcing policy a
    denial would mean system fonts are invisible to the build; the common path is
    unaffected because PyTeX's default (lmodern) fonts ship inside the tectonic
    bundle. A fontspec doc needing a specific system font should bake it into the
    sandbox image or pass it as a caller asset.
    """
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
    max_fsize_bytes: int,
    name: str | None = None,
) -> list[str]:
    """Assemble the full ``podman run ...`` argv wrapping ``inner_cmd``.

    Pure and unit-testable. ``inner_cmd`` is the tectonic argv already expressed
    in *container* paths (binary at :data:`CONTAINER_BINARY`, files under
    :data:`CONTAINER_WORKDIR`); this function only prepends the container
    launcher, its hardening flags, and the mounts. ``name`` gives the container
    a stable name so it can be force-removed if the wall-clock kill fires.

    ``max_memory_bytes`` is floored at :data:`MEMORY_FLOOR_BYTES` and
    ``max_fsize_bytes`` at :data:`FSIZE_FLOOR_BYTES`; both caps are always
    emitted (an unbounded container is a host OOM / disk-DoS vector).
    ``--ulimit fsize`` restores the per-file write cap lost with the in-process
    ``RLIMIT_FSIZE`` (its value is raw bytes, verified on Podman).
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

    # Always cap memory (floored), pids, cpu, and per-file write size (floored).
    memory = max(max_memory_bytes, MEMORY_FLOOR_BYTES)
    cmd += ["--memory", f"{memory}b"]
    cmd += ["--pids-limit", str(config.pids_limit)]
    cmd += ["--cpus", config.max_cpus]
    fsize = max(max_fsize_bytes, FSIZE_FLOOR_BYTES)
    cmd += ["--ulimit", f"fsize={fsize}:{fsize}"]
    cmd += [
        "--tmpfs",
        f"{_CONTAINER_HOME}:rw,nosuid,nodev,noexec,size={config.tmpfs_size}",
    ]

    cmd += ["-e", f"HOME={_CONTAINER_HOME}"]
    cmd += ["-e", f"XDG_CACHE_HOME={_CONTAINER_HOME}/.cache"]
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
