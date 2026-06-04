"""Value types for the blob-in / blob-out API: enums, request/result, errors.

Kept free of any heavy imports so a caller can describe a build without pulling
in marko, tectonic, or the render machinery.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping


def _empty_config() -> dict[str, object]:
    return {}


def _empty_assets() -> dict[str, bytes]:
    return {}


__all__ = [
    "ApiError",
    "BuildLimits",
    "BuildRequest",
    "BuildResult",
    "CompileError",
    "InputKind",
    "LimitError",
    "OutputKind",
    "TrustError",
    "TrustLevel",
]


class InputKind(Enum):
    """What the request bytes *are* - declared, never sniffed from a suffix.

    Declaring the kind removes suffix-confusion attacks and the implicit
    "``.py`` means execute me" coupling of the filesystem entry points.
    """

    MARKDOWN = "md"
    TEX = "tex"
    TEX_PY = "py"  # executes Python on load - TRUSTED only


class OutputKind(Enum):
    TEX = "tex"  # rendered LaTeX source
    PDF = "pdf"  # compiled via tectonic


class TrustLevel(Enum):
    """How much the source is trusted; the central axis of the security model.

    ``UNTRUSTED`` assumes the source is hostile (the default). ``TRUSTED`` is
    for first-party callers and unlocks Python execution and shell-escape.
    """

    UNTRUSTED = "untrusted"  # default; hostile input assumed
    SANDBOXED = "sandboxed"  # semi-trusted; wider packages, still no code/shell
    TRUSTED = "trusted"  # full power, incl. Python exec & shell-escape


class ApiError(RuntimeError):
    """Base class for every error the API raises deliberately."""


class TrustError(ApiError):
    """A capability was requested that the request's trust level forbids."""


class LimitError(ApiError):
    """A resource or size limit was exceeded (input, output, or build time)."""


class CompileError(ApiError):
    """tectonic was unavailable or failed to produce a PDF."""


@dataclass(frozen=True)
class BuildLimits:
    """Resource caps applied to a build (enforced hardest for untrusted input).

    ``cpu``/``memory``/``fsize`` map to POSIX ``setrlimit`` on the compile
    subprocess; ``wall_timeout_s`` is the subprocess wall-clock kill; the byte
    caps bound input, output, and the returned log.
    """

    wall_timeout_s: float = 30.0
    cpu_timeout_s: float = 30.0
    max_output_bytes: int = 25 * 1024 * 1024
    max_memory_bytes: int = 512 * 1024 * 1024
    max_fsize_bytes: int = 256 * 1024 * 1024
    max_input_bytes: int = 2 * 1024 * 1024
    max_tex_passes: int = 3
    max_log_chars: int = 100_000


@dataclass(frozen=True)
class BuildRequest:
    """A self-contained build job: source bytes in, never a path."""

    source: bytes
    input_kind: InputKind
    output_kind: OutputKind = OutputKind.PDF
    trust: TrustLevel = TrustLevel.UNTRUSTED
    variant: str | None = None
    config: Mapping[str, object] = field(default_factory=_empty_config)
    assets: Mapping[str, bytes] = field(default_factory=_empty_assets)  # name -> bytes
    limits: BuildLimits = field(default_factory=BuildLimits)


@dataclass(frozen=True)
class BuildResult:
    """The build output and metadata; the caller never sees a path."""

    output: bytes  # .tex or .pdf bytes
    output_kind: OutputKind
    log: str  # render/tectonic log, truncated to limits.max_log_chars
    warnings: tuple[str, ...]
    duration_s: float
