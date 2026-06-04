"""Concrete mitigations for untrusted input.

Pure helpers - no rendering, no subprocesses - so each can be tested in
isolation:

* asset-name validation (no absolute paths, no ``..``, no separators),
* Markdown eval-comment stripping (defuses the ``[//]: # "EXPR"`` hatch),
* package extraction + allowlist/blocklist enforcement on rendered LaTeX,
* a POSIX ``setrlimit`` pre-exec hook for the compile subprocess.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from ._models import LimitError, TrustError
from ._policy import DANGEROUS_PACKAGES

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from pathlib import Path

    from ._models import BuildLimits
    from ._policy import TrustPolicy

__all__ = [
    "enforce_input_size",
    "enforce_output_file_size",
    "enforce_output_size",
    "enforce_packages",
    "extract_packages",
    "filter_assets",
    "make_rlimit_preexec",
    "strip_markdown_eval_comments",
    "truncate_log",
    "validate_asset_name",
]

# `\usepackage[opts]{a,b}` / `\RequirePackage{c}` - capture the brace list.
_PACKAGE_RE = re.compile(
    r"\\(?:usepackage|RequirePackage)\s*(?:\[[^\]]*\])?\s*\{([^}]*)\}"
)

# A `[//]: # "EXPR"` Markdown comment (link-reference-definition escape hatch),
# in its quoted, parenthesised, or bare forms. Matched per line.
_EVAL_COMMENT_RE = re.compile(r"^[ \t]*\[//\]:[ \t]*#.*$", re.MULTILINE)


def validate_asset_name(name: str) -> str:
    """Return ``name`` if it is a safe, workdir-relative filename, else raise.

    Rejects absolute paths, parent traversal (``..``), path separators, NUL
    bytes, and empty/dot names so a caller-supplied asset cannot be written
    outside the per-request workdir.
    """
    if not name or name in {".", ".."}:
        raise TrustError(f"invalid asset name: {name!r}")
    if "\x00" in name:
        raise TrustError("asset name contains a NUL byte")
    if name.startswith(("/", "\\")) or (len(name) > 1 and name[1] == ":"):
        raise TrustError(f"asset name must be relative: {name!r}")
    if "/" in name or "\\" in name:
        raise TrustError(f"asset name must not contain a path separator: {name!r}")
    if ".." in name.split("."):
        raise TrustError(f"asset name must not traverse directories: {name!r}")
    return name


def strip_markdown_eval_comments(text: str) -> str:
    """Remove every ``[//]: # "EXPR"`` eval comment from Markdown ``text``.

    Defuses the Markdown code-execution hatch *before* conversion, so an
    untrusted document cannot ``eval`` arbitrary Python via the comment even if
    a future converter change forgot to gate it. Defence in depth alongside the
    trust-level check.
    """
    return _EVAL_COMMENT_RE.sub("", text)


def extract_packages(latex: str) -> set[str]:
    """All package names requested via ``\\usepackage``/``\\RequirePackage``."""
    return {
        name
        for match in _PACKAGE_RE.finditer(latex)
        for raw in match.group(1).split(",")
        if (name := raw.strip())
    }


def enforce_packages(latex: str, policy: TrustPolicy) -> None:
    """Reject rendered LaTeX that pulls a forbidden package.

    A dangerous package (code/shell/file surface) is refused for any
    non-trusted build; with allowlist enforcement on, anything outside the
    policy's allowlist is refused too. ``TRUSTED`` skips both checks.
    """
    if not policy.enforce_package_allowlist:
        return
    requested = extract_packages(latex)
    dangerous = sorted(requested & DANGEROUS_PACKAGES)
    if dangerous:
        raise TrustError(
            "document requests packages with a code-execution or file surface "
            + f"that {policy.level.value} input may not use: {', '.join(dangerous)}"
        )
    disallowed = sorted(requested - policy.package_allowlist)
    if disallowed:
        raise TrustError(
            f"document requests packages not on the {policy.level.value} "
            + f"allowlist: {', '.join(disallowed)}"
        )


def enforce_input_size(source: bytes, limits: BuildLimits) -> None:
    """Reject input larger than ``limits.max_input_bytes``."""
    if len(source) > limits.max_input_bytes:
        raise LimitError(
            f"input is {len(source)} bytes; the limit is {limits.max_input_bytes}"
        )


def enforce_output_size(output: bytes, limits: BuildLimits) -> None:
    """Reject output larger than ``limits.max_output_bytes``."""
    if len(output) > limits.max_output_bytes:
        raise LimitError(
            f"output is {len(output)} bytes; the limit is {limits.max_output_bytes}"
        )


def enforce_output_file_size(path: Path, limits: BuildLimits) -> None:
    """Reject an output file larger than the cap before it is read.

    Checks ``stat().st_size`` so a multi-gigabyte PDF is never loaded into the
    process (which would OOM); the in-memory check is the second line for the
    bytes once read.
    """
    size = path.stat().st_size
    if size > limits.max_output_bytes:
        raise LimitError(
            f"output file is {size} bytes; the limit is {limits.max_output_bytes}"
        )


def truncate_log(log: str, limits: BuildLimits) -> str:
    """Cap the returned log to ``limits.max_log_chars`` characters."""
    if len(log) <= limits.max_log_chars:
        return log
    head = log[: limits.max_log_chars]
    return head + f"\n... (log truncated at {limits.max_log_chars} chars)"


def make_rlimit_preexec(limits: BuildLimits) -> Callable[[], None] | None:
    """Build a ``preexec_fn`` that caps CPU, address space, and file size.

    Returns ``None`` where ``setrlimit`` is unavailable (non-POSIX), so the
    caller falls back to the wall-clock timeout alone. The hook also starts a
    new process group so the whole tree can be killed on timeout.
    """
    try:
        import os
        import resource
    except ImportError:  # pragma: no cover - POSIX-only module
        return None

    cpu = max(1, int(limits.cpu_timeout_s))
    mem = limits.max_memory_bytes
    fsize = limits.max_fsize_bytes

    def _preexec() -> None:  # pragma: no cover - runs in the forked child
        os.setpgrp()
        resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu))
        resource.setrlimit(resource.RLIMIT_FSIZE, (fsize, fsize))
        if mem > 0:
            resource.setrlimit(resource.RLIMIT_AS, (mem, mem))

    return _preexec


def filter_assets(
    assets: Mapping[str, bytes],
) -> dict[str, bytes]:
    """Validate every asset name, returning a name-checked copy."""
    return {validate_asset_name(name): data for name, data in assets.items()}
