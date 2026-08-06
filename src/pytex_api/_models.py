"""Value types for the blob-in and blob-out API.

This module holds the enums, the request type, the result type, and the
errors. It has no heavy imports, so a caller can describe a build without a
load of marko, tectonic, or the render machinery.
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
    """What the request bytes are, as the caller declares them.

    PyTeX never reads the kind from a file suffix. A declared kind removes
    suffix-confusion attacks. It also removes the implicit rule of the
    filesystem entry points that a `.py` suffix means "execute me".
    """

    MARKDOWN = "md"
    TEX = "tex"
    TEX_PY = "py"  # runs Python on load, for `trusted` builds only


class OutputKind(Enum):
    TEX = "tex"  # the rendered LaTeX source
    PDF = "pdf"  # compiled by the tectonic binary


class TrustLevel(Enum):
    """How much PyTeX trusts the source of a request.

    This is the central axis of the security model. `untrusted` is the default
    and assumes that the source is hostile. `trusted` is for first-party
    callers, and it unlocks Python execution and shell-escape.
    """

    UNTRUSTED = "untrusted"  # the default, which assumes hostile input
    SANDBOXED = "sandboxed"  # semi-trusted, wider packages, still no code or shell
    TRUSTED = "trusted"  # full power, including Python execution and shell-escape


class ApiError(RuntimeError):
    """Base class for every error that the API raises on purpose."""


class TrustError(ApiError):
    """The request asks for a capability that its trust level forbids."""


class LimitError(ApiError):
    """The input, the output, or the build time passed a limit."""


class CompileError(ApiError):
    """tectonic was not available, or it did not produce a PDF."""


@dataclass(frozen=True)
class BuildLimits:
    """Resource caps for one build, applied hardest to untrusted input.

    Attributes:
        wall_timeout_s: The wall-clock kill for the compile subprocess, in
            seconds.
        cpu_timeout_s: The POSIX `RLIMIT_CPU` cap for the compile subprocess,
            in seconds.
        max_output_bytes: The cap on the returned `.tex` bytes or PDF bytes.
        max_memory_bytes: The POSIX `RLIMIT_AS` cap, in bytes.
        max_fsize_bytes: The POSIX `RLIMIT_FSIZE` per-file write cap, in
            bytes.
        max_input_bytes: The cap on the source bytes of the request.
        max_tex_passes: The intended cap on the number of compile passes. No
            code reads this field today, because the tectonic binary picks its
            own pass count.
        max_log_chars: The cap on the returned log, in characters.
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
    """A self-contained build job that carries source bytes and never a path.

    Attributes:
        variant: The variant that wraps a converted Markdown source. `None`
            picks the default variant. The value has no effect on a `.tex` or
            a `.tex.py` source.
        config: The document-class parameters. They override the frontmatter
            of a Markdown source.
        assets: The inline assets, keyed by file name. PyTeX writes each one
            next to the rendered `.tex` file, before the render step. A name
            must be a plain file name, with no directory part. The `logos` and
            `footer_logos` config keys can name such an asset, so a caller can
            upload the logos of a document with the document itself.
    """

    source: bytes
    input_kind: InputKind
    output_kind: OutputKind = OutputKind.PDF
    trust: TrustLevel = TrustLevel.UNTRUSTED
    variant: str | None = None
    config: Mapping[str, object] = field(default_factory=_empty_config)
    assets: Mapping[str, bytes] = field(default_factory=_empty_assets)
    limits: BuildLimits = field(default_factory=BuildLimits)


@dataclass(frozen=True)
class BuildResult:
    """The build output and its metadata. The caller never sees a path.

    Attributes:
        output: The rendered `.tex` bytes or the PDF bytes. `output_kind`
            says which one.
        log: The render log and the tectonic log, truncated to
            `BuildLimits.max_log_chars`.
        warnings: The text that follows each `warning:` tag in the log.
        duration_s: The wall-clock time of the whole build, in seconds.
    """

    output: bytes
    output_kind: OutputKind
    log: str
    warnings: tuple[str, ...]
    duration_s: float
