"""Rootless Podman sandbox wrapper for untrusted and sandboxed compiles.

This module wraps the tectonic argv in a `podman run` call. That call confines
the build to a temporary, network-less, read-only container:

* `--network none` blocks the network. `pytex-sandbox-init` warms the bundle
  cache in advance, and an untrusted build also passes `--only-cached`, so
  tectonic never tries to fetch,
* `--read-only` makes the root filesystem read-only, and a size-capped `/tmp`
  tmpfs gives the build its scratch space,
* `--cap-drop ALL`, `--security-opt no-new-privileges`, and the default
  seccomp profile of Podman cut the set of kernel calls that the build can
  make,
* `--memory`, `--pids-limit`, and `--cpus` set the cgroups v2 resource caps,
* the temporary work directory of the request is the only read-write mount.
  Podman relabels it for SELinux with `:Z`. Podman mounts the warmed bundle
  cache as a temporary overlay with `:O`, so tectonic gets a writable view and
  the host cache never changes.

tectonic runs from the image itself, because the image carries the binary, its
shared libraries, and fontconfig. So Podman mounts no host system path as an
executable. To mount a statically-linked host binary instead, set
`tectonic_in_image=False`.

The sandbox is defense in depth on top of the trust gates in the render layer
and the `setrlimit` and timeout floor in `pytex_api._compile`. `render_blob`
knows nothing about the sandbox. The `TrustPolicy` selects the wrapper.
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

# The mount points and paths inside the container.
CONTAINER_WORKDIR = "/work"
CONTAINER_BINARY = "/work/tectonic-bin"  # used only with a mounted host binary
CONTAINER_CACHE = "/cache"
_CONTAINER_HOME = "/tmp"  # writable tmpfs for the fontconfig and XDG scratch

# The default image is a small Fedora base. It carries tectonic, the shared
# libraries of tectonic, and fontconfig, all from the distro repositories. The
# image build is a privileged warm-up step (see `build_sandbox_image`), and an
# untrusted request never reaches the network. tectonic comes from the image,
# so PyTeX never has to put a host binary into the container. Such a host
# binary can link against libraries that the base image does not have.
_DEFAULT_IMAGE = "localhost/pytex-tectonic:latest"
# This module pins the base image by digest, not by the moving `:latest` tag.
# So the build is reproducible, and an auditor can check the supply chain.
_BASE_IMAGE = (
    "registry.fedoraproject.org/fedora-minimal"
    "@sha256:7d847227f0f90b4d45566c9a2ba67b5d36a286b798dbdf27f24d2c02a23b6489"
)
# tectonic is not a Fedora package. The image build installs a pinned upstream
# release and verifies its sha256, instead of a pipe from the latest installer
# into a shell. The distro supplies the shared libraries that tectonic links,
# which are graphite2 and openssl, and fontconfig for a fontspec document.
# harfbuzz and freetype are statically bundled in the tectonic binary.
_TECTONIC_VERSION = "0.16.9"
# The upstream release asset per architecture, with its sha256. Podman builds
# the image natively on the host, so the asset must match the CPU
# architecture of that host. x86_64 uses the glibc build, whose shared
# libraries come from the install line below. Upstream ships only a
# statically-linked musl build for aarch64. A hard-coded x86_64 asset caused
# an "exec format error" when Podman built the image on ARM.
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
# A `platform.machine()` spelling -> a key in `_TECTONIC_ASSETS`.
_ARCH_ALIASES: dict[str, str] = {
    "x86_64": "x86_64",
    "amd64": "x86_64",
    "aarch64": "aarch64",
    "arm64": "aarch64",
}


def _tectonic_url(target: str) -> str:
    """Return the upstream release URL for a `<arch>-<vendor>-<os>-<abi>` target."""
    return (
        "https://github.com/tectonic-typesetting/tectonic/releases/download/"
        f"tectonic%40{_TECTONIC_VERSION}/"
        f"tectonic-{_TECTONIC_VERSION}-{target}.tar.gz"
    )


def _containerfile(machine: str | None = None) -> str:
    """Build the text of the sandbox Containerfile for one CPU architecture.

    The architecture picks the tectonic download URL and its sha256, so the
    image builds correctly on an x86_64 host and on an aarch64 host. The
    aarch64 musl binary is static, so the extra `graphite2` and `openssl-libs`
    packages that it does not link do no harm there. Both architectures need
    `fontconfig` for a fontspec document.

    Args:
        machine: A `platform.machine()` spelling. `None` reads the
            architecture of the host.

    Returns:
        The full Containerfile text.

    Raises:
        RuntimeError: PyTeX has no tectonic asset for this architecture.
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
# Floors for a non-trusted build, so a limit of zero or less cannot remove a
# cap. A container with no cap can exhaust the host memory or the host disk.
MEMORY_FLOOR_BYTES = 256 * 1024 * 1024
FSIZE_FLOOR_BYTES = 64 * 1024 * 1024

# The host font directories and fontconfig directories. PyTeX mounts each one
# read-only when it exists, so a fontspec document can see the system fonts. A
# basic lmodern build needs none of them, because those fonts come from the
# tectonic bundle.
_DEFAULT_FONT_DIRS: tuple[str, ...] = (
    "/usr/share/fonts",
    "/usr/local/share/fonts",
    "/usr/share/fontconfig",
    "/etc/fonts",
)


def _default_cache_dir() -> Path:
    """Return the bundle cache path of tectonic.

    Returns:
        `$XDG_CACHE_HOME/Tectonic`, or `~/.cache/Tectonic` when
        `XDG_CACHE_HOME` is not set.
    """
    xdg = os.environ.get("XDG_CACHE_HOME")
    base = Path(xdg) if xdg else Path.home() / ".cache"
    return base / "Tectonic"


@dataclass(frozen=True)
class SandboxConfig:
    """The settings of the Podman sandbox. Every one has a safe default."""

    image: str = _DEFAULT_IMAGE
    cache_dir: Path = field(default_factory=_default_cache_dir)
    font_dirs: tuple[str, ...] = _DEFAULT_FONT_DIRS
    pids_limit: int = _DEFAULT_PIDS_LIMIT
    max_cpus: str = _DEFAULT_MAX_CPUS
    tmpfs_size: str = _DEFAULT_TMPFS_SIZE
    # `None` -> the built-in default seccomp profile of Podman, which is the
    # recommended value. A path -> a custom JSON profile, passed with
    # `--security-opt seccomp=`.
    seccomp_profile: Path | None = None
    # Mount each host font directory that exists read-only into the container.
    mount_fonts: bool = True
    # `True` -> run the tectonic binary of the image. This is the recommended
    # value, because the image carries the binary and its shared libraries.
    # `False` -> mount a host binary at `CONTAINER_BINARY`, which is only safe
    # with a statically-linked tectonic.
    tectonic_in_image: bool = True


def podman_available() -> bool:
    """Report whether a `podman` binary is on PATH."""
    return which("podman") is not None


def sandbox_image_present(image: str = _DEFAULT_IMAGE) -> bool:
    """Report whether `image` already exists on this host.

    The check never uses the network.
    """
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
    """Build the tectonic sandbox image.

    This is a privileged warm-up step, and it needs the network. Podman
    installs `tectonic` and `fontconfig` into a Fedora base. The build picks
    the tectonic binary for the CPU architecture of the build host.

    Run this step once, out of band. Never call it from a request path that
    serves untrusted input.

    Raises:
        RuntimeError: `podman build` exited non-zero.
    """
    # The "-" argument reads the Containerfile from stdin with no build
    # context. The file has no COPY and no ADD, so Podman does not need to
    # send the whole repository to the builder.
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


# One warm-up document per variant that matters offline. Each one carries the
# real preamble of its variant, which holds the HSRT report fonts and the
# packages of the meeting protocol header. These documents pull the exact
# bundle resources that the offline build needs, which a bare "# Warm" stub
# would not. The offline build runs with `--network none` and
# `--only-cached`. So a real report or meeting protocol finds everything in
# the cache on its first compile.
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
    """Render each warm-up sample to a `.tex` file in the `work` directory.

    The render runs under the `trusted` policy, so each variant preamble comes
    out exactly as a real build writes it. This function only renders. It uses
    no network and no container.

    Returns:
        The file names of the rendered `.tex` files, in sample order.
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
    """Assemble the `podman run` argv that warms the cache from `tex_name`.

    The function is pure, so a unit test can call it directly. The network
    stays on, which is the Podman default. Podman mounts the cache read-write
    with the shared `:z` relabel, and not with the private `:Z` relabel. The
    cache is the shared lower layer. A later request container reads it
    through `:O`, and a `trusted` build on the host reads it directly. Under
    enforcing SELinux, a private MCS category from `:Z` would deny both
    readers. `:z` is safe here, because the cache lives in the `$HOME` of the
    user, who owns it. A shared system directory would be a different case.
    """
    return [
        "podman",
        "run",
        "--rm",
        # The one-time privileged warm-up uses the host network namespace, so
        # it can fetch the bundle even where rootless slirp or pasta
        # networking is not available. This is not the untrusted path, which
        # always runs with `--network none`.
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
    """Fill the bundle cache by running the tectonic binary of the image.

    This is a one-time privileged warm-up. It runs the sandbox image online
    with the cache mounted read-write. So the exact tectonic version that the
    confined builds use writes the fetched bundle into the host cache.

    The warm-up runs one compile per variant that matters: plain, report, and
    the two meeting protocol variants. So an offline request finds the
    preamble resources of a real document in the cache. The offline request
    runs with `--network none` and `--only-cached`.

    Without this step, the cache can miss and the offline request then fails.
    A cache warmed by a host tectonic of a different version can miss. A cache
    warmed by a minimal stub without the report fonts and the meeting protocol
    fonts can also miss. Never call this function from a request path that
    serves untrusted input.

    Raises:
        RuntimeError: One warm-up compile exited non-zero.
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
    """Build the read-only mount flags for the host font directories that exist.

    SELinux note: Podman mounts these plain with `:ro` and does not relabel
    them. A `:z` relabel of a shared system directory such as
    `/usr/share/fonts` fails rootless with `lsetxattr ... operation not
    permitted`, because the user does not own those files. So a relabel is not
    an option here.

    Under a strict enforcing policy, SELinux can then hide the system fonts
    from the build. The common path does not change, because the default
    lmodern fonts of PyTeX come from the tectonic bundle. If a fontspec
    document needs one specific system font, put that font into the sandbox
    image, or pass it as an inline asset.

    Returns:
        The `-v` flags and their mount arguments, in one flat list.
    """
    if not config.mount_fonts:
        return []
    return [
        flag
        for src in config.font_dirs
        if Path(src).is_dir()
        for flag in ("-v", f"{src}:{src}:ro")
    ]


def build_podman_cmd(
    workdir: Path,
    inner_cmd: list[str],
    config: SandboxConfig,
    *,
    max_memory_bytes: int,
    max_fsize_bytes: int,
    name: str | None = None,
) -> list[str]:
    """Assemble the full `podman run ...` argv around `inner_cmd`.

    The function is pure, so a unit test can call it directly. It only puts
    the container launcher, the hardening flags, and the mounts in front of
    `inner_cmd`.

    Args:
        inner_cmd: The tectonic argv, already written in container paths. The
            binary sits at `CONTAINER_BINARY`, and the files under
            `CONTAINER_WORKDIR`.
        max_memory_bytes: The memory cap, floored at `MEMORY_FLOOR_BYTES`.
        max_fsize_bytes: The per-file write cap, floored at
            `FSIZE_FLOOR_BYTES`. `--ulimit fsize` carries it, and its value is
            raw bytes on Podman. This cap replaces the in-process
            `RLIMIT_FSIZE`, which the container path does not apply.
        name: A stable container name, so the caller can force-remove the
            container after a wall-clock kill. `None` lets Podman pick a name.

    Returns:
        The full argv. Both resource caps are always present, because a
        container with no cap can exhaust the host memory or the host disk.
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
    # A `None` profile needs no flag. Podman then applies its own default.

    # Always cap the memory, the process count, the CPU count, and the
    # per-file write size. The memory cap and the write cap get a floor.
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

    # Mount the warmed bundle cache as a temporary overlay. tectonic gets a
    # writable view, the host cache never changes, and Podman does the
    # relabel.
    cmd += ["-v", f"{config.cache_dir}:{CONTAINER_CACHE}:O"]
    cmd += _existing_font_mounts(config)
    # The temporary work directory of the request is the only read-write
    # mount. Podman relabels it for SELinux with `:Z`, so the container can
    # read it and write it under an enforcing policy.
    cmd += ["-v", f"{workdir}:{CONTAINER_WORKDIR}:rw,Z"]
    cmd += ["--workdir", CONTAINER_WORKDIR]
    cmd.append(config.image)
    cmd += inner_cmd
    return cmd
