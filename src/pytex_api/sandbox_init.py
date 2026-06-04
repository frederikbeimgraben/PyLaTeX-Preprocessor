"""``pytex-sandbox-init`` - one-shot setup for offline UNTRUSTED PDF builds.

A new user who wants confined (UNTRUSTED / SANDBOXED) PDF compiles needs two
out-of-band, privileged steps done once: build the Podman sandbox image and
warm the tectonic bundle cache so the offline (``--network none`` +
``--only-cached``) request path does not cache-miss. This console script does
both, with friendly preflight checks and error messages instead of raw
``podman`` stderr, so the user never has to guess why a confined build refuses
to run.

It is the *privileged warm-up* path from :mod:`pytex_api._sandbox`; it must
never be wired into a request handler.
"""

from __future__ import annotations

import argparse
import contextlib
import os
from pathlib import Path
from typing import cast

from pytex_builder.console import Console

from ._sandbox import (
    SandboxConfig,
    build_sandbox_image,
    podman_available,
    sandbox_image_present,
    warm_sandbox_cache,
)

__all__ = ["main"]


def _current_user_keys() -> set[str]:
    """Identifiers a subuid/subgid line might be keyed by (login name or uid).

    Empty on non-POSIX or when the user cannot be resolved, which the caller
    reads as "skip the check" rather than "misconfigured".
    """
    if not hasattr(os, "getuid"):
        return set()
    uid = os.getuid()
    keys = {str(uid)}
    try:
        import pwd
    except ImportError:
        return keys
    with contextlib.suppress(KeyError):
        keys.add(pwd.getpwuid(uid).pw_name)
    return keys


def _has_subid_range(path: Path, keys: set[str]) -> bool:
    """Whether *path* (``/etc/subuid`` or ``/etc/subgid``) lists one of *keys*."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return False
    return any(line.split(":", 1)[0] in keys for line in lines)


def _subid_configured() -> bool:
    """Best-effort check for the rootless subuid/subgid prerequisite.

    Rootless Podman maps container UIDs/GIDs through ``/etc/subuid`` and
    ``/etc/subgid``; without a range for the user, ``podman build``/``run``
    fails with a ``newuidmap``/``subuid`` error. Returns ``True`` (skip the
    check) when the user cannot be identified, so a false negative never blocks
    an otherwise-working setup.
    """
    keys = _current_user_keys()
    if not keys:
        return True
    return _has_subid_range(Path("/etc/subuid"), keys) and _has_subid_range(
        Path("/etc/subgid"), keys
    )


def _friendly_error(message: str) -> str:
    """Map raw podman/tectonic failure text to an actionable hint.

    Falls back to the original message when nothing matches - still better than
    swallowing it.
    """
    low = message.lower()
    if any(token in low for token in ("subuid", "subgid", "newuidmap", "newgidmap")):
        return (
            "rootless podman is missing subuid/subgid ranges for your user. "
            "Add them and re-run, e.g.:\n"
            "  sudo usermod --add-subuids 100000-165535 "
            "--add-subgids 100000-165535 $USER\n"
            "  podman system migrate"
        )
    if "cannot connect" in low or "connection refused" in low:
        return (
            "could not reach the podman service; run 'podman info' to diagnose. "
            "On a fresh install 'podman system migrate' often fixes it"
        )
    if "no space left" in low:
        return "container storage is out of disk space; free some and re-run"
    return message


def _check_podman(console: Console) -> bool:
    """Fatal preflight: podman must be installed. Returns ``False`` if not."""
    if podman_available():
        return True
    console.error("podman is not installed or not on PATH")
    console.hint(
        "install Podman (e.g. 'sudo dnf install podman' or 'sudo apt install "
        + "podman'); rootless mode needs no daemon"
    )
    return False


def _warn_if_not_rootless(console: Console) -> None:
    """Soft preflight: warn (do not fail) when subuid/subgid look unconfigured."""
    if _subid_configured():
        return
    console.warn("rootless podman may not be fully configured")
    console.hint(
        "no subuid/subgid range found for your user in /etc/subuid|/etc/subgid; "
        + "if the build fails, add one (see 'man subuid') and run "
        + "'podman system migrate'"
    )


def _ensure_image(
    config: SandboxConfig, console: Console, *, force_build: bool
) -> None:
    """Build the sandbox image unless it already exists (and not forced)."""
    if not force_build and sandbox_image_present(config.image):
        console.note(f"sandbox image {config.image} already present; skipping build")
        return
    console.step(f"Building sandbox image {config.image} (this needs network)")
    build_sandbox_image(config.image)


def main(argv: list[str] | None = None, *, console: Console | None = None) -> int:
    """Build the sandbox image and warm the bundle cache; return an exit code."""
    parser = argparse.ArgumentParser(
        prog="pytex-sandbox-init",
        description=(
            "Build the Podman sandbox image and warm the tectonic bundle cache "
            "so UNTRUSTED/SANDBOXED PDF builds can run fully offline."
        ),
    )
    _ = parser.add_argument(
        "--image", default=None, help="sandbox image tag (default: the built-in)"
    )
    _ = parser.add_argument(
        "--skip-warm",
        action="store_true",
        help="build the image but skip the bundle cache warm-up",
    )
    _ = parser.add_argument(
        "--force-build",
        action="store_true",
        help="rebuild the image even if it already exists",
    )
    ns = parser.parse_args(argv)
    image = cast("str | None", ns.image)
    skip_warm = cast("bool", ns.skip_warm)
    force_build = cast("bool", ns.force_build)

    out = console or Console()
    if not _check_podman(out):
        return 1
    _warn_if_not_rootless(out)

    config = SandboxConfig() if image is None else SandboxConfig(image=image)
    try:
        _ensure_image(config, out, force_build=force_build)
        if skip_warm:
            out.note(
                "skipping cache warm-up (--skip-warm); offline builds may "
                + "cache-miss until warmed"
            )
        else:
            out.step("Warming the tectonic bundle cache (downloads once)")
            warm_sandbox_cache(config)
    except RuntimeError as exc:
        out.error("sandbox initialisation failed")
        out.hint(_friendly_error(str(exc)))
        return 1

    out.success(
        f"sandbox image {config.image} built (cache not warmed)"
        if skip_warm
        else f"sandbox ready: image {config.image} built and bundle cache warmed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
