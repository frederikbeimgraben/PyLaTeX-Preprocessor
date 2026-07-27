"""`pytex-sandbox-init`: one-time setup for offline, confined PDF builds.

A confined PDF build is an `untrusted` or a `sandboxed` build. Before the
first one, you must do two privileged steps once, out of band:

1. Build the Podman sandbox image.
2. Warm the tectonic bundle cache, so the offline request path finds every
   resource. That path runs with `--network none` and `--only-cached`.

This console script does both. It runs preflight checks and prints clear
errors instead of raw `podman` stderr. So you do not have to guess why a
confined build refuses to run.

This module is the privileged warm-up path of `pytex_api._sandbox`. Never wire
it into a request handler.
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
    """Return the identifiers that a subuid or subgid line can use as its key.

    A line uses the login name or the numeric user ID.

    Returns:
        The set of identifiers. The set is empty on a non-POSIX platform, and
        when PyTeX cannot resolve the user. The caller reads an empty set as
        "skip the check", not as "the host is misconfigured".
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
    """Report whether `path` lists one of `keys`.

    Args:
        path: `/etc/subuid` or `/etc/subgid`.
        keys: The login name and the numeric user ID of the current user.
    """
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return False
    return any(line.split(":", 1)[0] in keys for line in lines)


def _subid_configured() -> bool:
    """Check the subuid and subgid ranges that rootless Podman needs.

    Rootless Podman maps the user IDs and group IDs of a container through
    `/etc/subuid` and `/etc/subgid`. Without a range for the user, `podman
    build` and `podman run` fail with a `newuidmap` or `subuid` error.

    Returns:
        `True` when a range exists, and also when PyTeX cannot identify the
        user. The second case skips the check, so a false negative never
        blocks a setup that works.
    """
    keys = _current_user_keys()
    if not keys:
        return True
    return _has_subid_range(Path("/etc/subuid"), keys) and _has_subid_range(
        Path("/etc/subgid"), keys
    )


def _friendly_error(message: str) -> str:
    """Map raw podman or tectonic failure text to a hint the user can act on.

    Returns:
        The hint, or the original message when no pattern matches. The
        original message is still better than no message.
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
    """Run the fatal preflight check that Podman is installed.

    Returns:
        `True` when `podman` is on PATH. `False` after the function printed
        the error and the install hint. The caller must then stop.
    """
    if podman_available():
        return True
    console.error("podman is not installed or not on PATH")
    console.hint(
        "install Podman (e.g. 'sudo dnf install podman' or 'sudo apt install "
        + "podman'); rootless mode needs no daemon"
    )
    return False


def _warn_if_not_rootless(console: Console) -> None:
    """Warn when the subuid and subgid ranges look unconfigured.

    This is a soft preflight check. It only warns, and it never fails the
    setup, because the check can produce a false negative.
    """
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
    """Build the sandbox image unless it already exists.

    Args:
        force_build: Rebuild the image even when it already exists.

    Raises:
        RuntimeError: `podman build` exited non-zero.
    """
    if not force_build and sandbox_image_present(config.image):
        console.note(f"sandbox image {config.image} already present; skipping build")
        return
    console.step(f"Building sandbox image {config.image} (this needs network)")
    build_sandbox_image(config.image)


def main(argv: list[str] | None = None, *, console: Console | None = None) -> int:
    """Build the sandbox image and warm the bundle cache.

    Args:
        argv: The command-line arguments. `None` reads `sys.argv`.
        console: The console that prints the progress. `None` makes a new one.

    Returns:
        0 after a successful setup. 1 when Podman is missing, or when a step
        failed. The function prints a hint before it returns 1.
    """
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
