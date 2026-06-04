"""Blob-in / blob-out wrapper around PyTeX.

Hand it **source bytes** (Markdown, ``.tex``, or ``.tex.py``) and a declared
:class:`InputKind`; get back **result bytes** - rendered ``.tex`` or a compiled
PDF - without ever touching the filesystem yourself. All I/O happens inside a
per-request temp directory that is removed when the call returns.

The :class:`TrustLevel` on each request is the security axis, with three levels:
``UNTRUSTED`` (the default) assumes hostile input and disables every
code-execution surface (Python import, Markdown ``eval`` comments, ``.tex``
``pytex(...)`` replacements, shell-escape), enforces the strict package
allowlist, and caps build resources; ``SANDBOXED`` is semi-trusted - still no
code or shell surface, but a wider package allowlist
(:data:`SANDBOXED_EXTRA_PACKAGES`); ``TRUSTED`` unlocks the full pipeline for
first-party documents.

``render_blob`` is synchronous; ``render_blob_async`` offloads the blocking work
under a copied context so concurrent async requests stay isolated (the
``_render_depth`` ``ContextVar`` fix is what makes that correct).

Example::

    from pytex_api import BuildRequest, InputKind, OutputKind, render_blob

    result = render_blob(
        BuildRequest(
            source=b"# Hello\\n\\nWorld.",
            input_kind=InputKind.MARKDOWN,
            output_kind=OutputKind.TEX,
        )
    )
    assert b"Hello" in result.output
"""

from __future__ import annotations

import asyncio
import contextvars
import io
import shutil
import tempfile
from pathlib import Path
from time import perf_counter

from pytex_builder.console import Console

from ._compile import compile_to_pdf
from ._models import (
    ApiError,
    BuildLimits,
    BuildRequest,
    BuildResult,
    CompileError,
    InputKind,
    LimitError,
    OutputKind,
    TrustError,
    TrustLevel,
)
from ._policy import (
    DANGEROUS_PACKAGES,
    PACKAGE_ALLOWLIST,
    SANDBOXED_EXTRA_PACKAGES,
    TrustPolicy,
    policy_for,
)
from ._render import render_to_latex
from ._security import (
    enforce_input_size,
    enforce_output_size,
    filter_assets,
    truncate_log,
)

__all__ = [
    "DANGEROUS_PACKAGES",
    "PACKAGE_ALLOWLIST",
    "SANDBOXED_EXTRA_PACKAGES",
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
    "TrustPolicy",
    "policy_for",
    "render_blob",
    "render_blob_async",
]


def _collect_warnings(log: str) -> tuple[str, ...]:
    """Pull ``warning:``-tagged lines out of the captured console output."""
    return tuple(
        line.split("warning:", 1)[1].strip()
        for line in log.splitlines()
        if "warning:" in line
    )


def _render_or_compile_error(
    req: BuildRequest, policy: TrustPolicy, workdir: Path
) -> str:
    """Render to LaTeX, mapping malformed-source failures to ``CompileError``.

    The render machinery raises raw exceptions on hostile or broken input - a
    Python ``SyntaxError`` or a non-node ``__pytex__`` (surfaced as a
    ``pytex_builder`` ``BuildError``), an ``eval`` failure in a ``pytex(...)``
    replacement, or a Markdown parse error. Those would otherwise reach the
    caller as a bare :class:`Exception`, forcing a blanket 500. We translate
    them to a :class:`CompileError` carrying a generic message - the underlying
    exception is chained for server-side logs but never embedded in the
    message, so no temp path or stacktrace leaks to the client. Our own typed
    :class:`ApiError`s (trust gate, limits, package allowlist) pass through
    unchanged.
    """
    try:
        return render_to_latex(req, policy, workdir)
    except ApiError:
        raise
    except Exception as exc:
        raise CompileError(
            "source could not be rendered: malformed or invalid input"
        ) from exc


def render_blob(req: BuildRequest) -> BuildResult:
    """Render a :class:`BuildRequest` to a :class:`BuildResult`, synchronously.

    Runs the whole pipeline inside a fresh ``mkdtemp`` workdir that is removed
    before returning. Raises :class:`TrustError`, :class:`LimitError`, or
    :class:`CompileError` (all :class:`ApiError`) on policy or build failure.
    """
    start = perf_counter()
    enforce_input_size(req.source, req.limits)
    policy = policy_for(req.trust)
    # Validate asset names once, up front, and carry the checked dict forward -
    # the compile step writes *this*, never the raw `req.assets`, so safety no
    # longer hinges on call order.
    assets = filter_assets(req.assets)

    stream = io.StringIO()
    console = Console(stream=stream)
    workdir = Path(tempfile.mkdtemp(prefix="pytex-api-"))
    try:
        latex = _render_or_compile_error(req, policy, workdir)
        if req.output_kind is OutputKind.TEX:
            output = latex.encode("utf-8")
            enforce_output_size(output, req.limits)
            log = truncate_log(stream.getvalue(), req.limits)
            return BuildResult(
                output=output,
                output_kind=OutputKind.TEX,
                log=log,
                warnings=_collect_warnings(stream.getvalue()),
                duration_s=perf_counter() - start,
            )
        pdf, compile_log = compile_to_pdf(latex, req, policy, workdir, console, assets)
        full_log = stream.getvalue() + compile_log
        log = truncate_log(full_log, req.limits)
        return BuildResult(
            output=pdf,
            output_kind=OutputKind.PDF,
            log=log,
            # Include tectonic's own `warning:` lines, consistent with the TEX
            # path (which only has the console stream to draw from).
            warnings=_collect_warnings(full_log),
            duration_s=perf_counter() - start,
        )
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


async def render_blob_async(req: BuildRequest) -> BuildResult:
    """Async wrapper: run :func:`render_blob` off the event loop, isolated.

    The work is offloaded to the default executor under a *copied* context, so
    the ``_render_depth`` ``ContextVar`` (and any future render-time context
    var) is private to this request - concurrent async builds cannot corrupt
    each other's box-nesting depth.
    """
    loop = asyncio.get_running_loop()
    ctx = contextvars.copy_context()

    def _call() -> BuildResult:
        return ctx.run(render_blob, req)

    return await loop.run_in_executor(None, _call)


# Re-exported for callers that build their own limits but want the default
# numbers as a starting point.
DEFAULT_LIMITS: BuildLimits = BuildLimits()
