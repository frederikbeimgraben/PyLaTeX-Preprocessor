"""Concrete mitigations for untrusted input.

Every function here is pure. None renders, and none starts a subprocess, so a
test can call each one in isolation. The module holds:

* the asset-name check, which refuses an absolute path, a `..` component, and
  a path separator,
* the removal of the Markdown `[//]: # "EXPR"` eval comments,
* the package extraction and the allowlist and blocklist checks on rendered
  LaTeX,
* a POSIX `setrlimit` pre-exec hook for the compile subprocess.
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

# Matches `\usepackage[opts]{a,b}` and `\RequirePackage{c}`, and captures the
# brace list.
_PACKAGE_RE = re.compile(
    r"\\(?:usepackage|RequirePackage)\s*(?:\[[^\]]*\])?\s*\{([^}]*)\}"
)

# Matches a `[//]: # "EXPR"` Markdown comment, one line at a time. The comment
# is a link reference definition, which Markdown uses as a comment form. The
# pattern covers the quoted form, the parenthesized form, and the bare form.
_EVAL_COMMENT_RE = re.compile(r"^[ \t]*\[//\]:[ \t]*#.*$", re.MULTILINE)


def validate_asset_name(name: str) -> str:
    """Return `name` when it is a safe file name inside the work directory.

    The check refuses an absolute path, a `..` component, a path separator, a
    NUL byte, an empty name, and a dot name. So PyTeX cannot write an asset
    of the caller outside the temporary work directory of the request.

    Raises:
        TrustError: The name fails one of the checks above.
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
    """Remove every `[//]: # "EXPR"` eval comment from the Markdown `text`.

    This closes the Markdown code-execution surface before the conversion
    starts. So an untrusted document cannot run Python through the comment,
    even after a later change to the Markdown converter drops its own gate.
    This is defense in depth next to the trust-level check.
    """
    return _EVAL_COMMENT_RE.sub("", text)


def extract_packages(latex: str) -> set[str]:
    """Return every package name that `\\usepackage` or `\\RequirePackage` names."""
    return {
        name
        for match in _PACKAGE_RE.finditer(latex)
        for raw in match.group(1).split(",")
        if (name := raw.strip())
    }


def enforce_packages(latex: str, policy: TrustPolicy) -> None:
    """Reject rendered LaTeX that requires a forbidden package.

    PyTeX refuses a dangerous package for every non-trusted build. A dangerous
    package has a code surface, a shell surface, or a file surface. When the
    policy applies the package allowlist, PyTeX also refuses every package
    outside that allowlist. A `trusted` build skips both checks.

    Raises:
        TrustError: The LaTeX requires a dangerous package, or a package
            outside the allowlist of the policy.
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
    """Reject input larger than `limits.max_input_bytes`.

    Raises:
        LimitError: The source is larger than the cap.
    """
    if len(source) > limits.max_input_bytes:
        raise LimitError(
            f"input is {len(source)} bytes; the limit is {limits.max_input_bytes}"
        )


def enforce_output_size(output: bytes, limits: BuildLimits) -> None:
    """Reject output larger than `limits.max_output_bytes`.

    Raises:
        LimitError: The output is larger than the cap.
    """
    if len(output) > limits.max_output_bytes:
        raise LimitError(
            f"output is {len(output)} bytes; the limit is {limits.max_output_bytes}"
        )


def enforce_output_file_size(path: Path, limits: BuildLimits) -> None:
    """Reject an output file larger than the cap before anything reads it.

    The check reads `stat().st_size`, so a multi-gigabyte PDF never lands in
    the process and cannot cause an out-of-memory kill. The in-memory check is
    the second line of defense for the bytes once read.

    Raises:
        LimitError: The file is larger than `limits.max_output_bytes`.
    """
    size = path.stat().st_size
    if size > limits.max_output_bytes:
        raise LimitError(
            f"output file is {size} bytes; the limit is {limits.max_output_bytes}"
        )


def truncate_log(log: str, limits: BuildLimits) -> str:
    """Cap the returned log at `limits.max_log_chars` characters.

    Returns:
        The log itself when it fits, or the first `max_log_chars` characters
        with a truncation note added.
    """
    if len(log) <= limits.max_log_chars:
        return log
    head = log[: limits.max_log_chars]
    return head + f"\n... (log truncated at {limits.max_log_chars} chars)"


def make_rlimit_preexec(limits: BuildLimits) -> Callable[[], None] | None:
    """Build a `preexec_fn` that caps the CPU, the address space, and the file size.

    The hook also starts a new process group, so PyTeX can kill the whole
    process tree on a timeout.

    Returns:
        The pre-exec hook, or `None` where `setrlimit` is not available, which
        means a non-POSIX platform. The caller then has the wall-clock timeout
        alone.
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
    """Check every asset name and return a name-checked copy of the mapping.

    Raises:
        TrustError: One name is not a safe file name.
    """
    return {validate_asset_name(name): data for name, data in assets.items()}
