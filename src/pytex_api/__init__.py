"""Blob-in and blob-out wrapper around PyTeX.

You give this package source bytes (Markdown, `.tex`, or `.tex.py`) and a
declared `InputKind`. You get back result bytes. The bytes are a rendered
`.tex` file or a compiled PDF. You never touch the filesystem yourself. All
reads and writes happen inside a temporary work directory that PyTeX removes
when the call returns.

The `TrustLevel` of a request is the security axis. It has three values.
`untrusted` is the default. It assumes hostile input, closes every
code-execution surface, applies the strict package allowlist, and caps the
build resources. The closed surfaces are the Python import, the Markdown
`eval` comments, the inline `pytex(...)` markers, and shell-escape.

`sandboxed` is semi-trusted. It keeps the code surface and the shell surface
closed, but it adds a wider package allowlist (`SANDBOXED_EXTRA_PACKAGES`).
`trusted` unlocks the whole pipeline for first-party documents.

`render_blob` is synchronous. `render_blob_async` moves the blocking work to
an executor under a copy of the current context, so concurrent async requests
stay isolated. The copy is what makes the `_render_depth` `ContextVar`
correct.

Example:
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
    """Return the text that follows each `warning:` tag in the captured log."""
    return tuple(
        line.split("warning:", 1)[1].strip()
        for line in log.splitlines()
        if "warning:" in line
    )


def _render_or_compile_error(
    req: BuildRequest, policy: TrustPolicy, workdir: Path
) -> str:
    """Render to LaTeX and map a malformed-source failure to `CompileError`.

    The render step raises raw exceptions on hostile or broken input. One
    example is a Python `SyntaxError`. Another is a `__pytex__` name that is
    not a TeX node, which the render step reports as a `pytex_builder`
    `BuildError`. A failed `eval` in an inline `pytex(...)` marker and a
    Markdown parse error do the same. Such an exception reaches the caller as
    a bare `Exception` and forces a blanket 500.

    This function translates those exceptions into a `CompileError` with a
    generic message. It chains the original exception for the server-side log,
    but it never puts that text into the message. So no temporary path and no
    stack trace leaks to the client. The typed `ApiError` classes of this API
    pass through unchanged. These cover the trust gate, the limits, and the
    package allowlist.

    Returns:
        The rendered LaTeX source.

    Raises:
        CompileError: The render step failed for a reason other than an
            `ApiError`.
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
    """Render a `BuildRequest` to a `BuildResult` synchronously.

    PyTeX runs the whole build inside a fresh temporary work directory from
    `mkdtemp`, and removes that directory before this function returns. Every
    error below is a subclass of `ApiError`.

    Returns:
        The result bytes, the log, the warnings, and the build duration.

    Raises:
        TrustError: The request asks for a capability that its trust level
            forbids.
        LimitError: The input, the output, or the build time passed a limit.
        CompileError: The render step or the compile step failed.
    """
    start = perf_counter()
    enforce_input_size(req.source, req.limits)
    policy = policy_for(req.trust)
    # Validate the asset names once, up front, and carry the checked dict
    # forward. The compile step writes this dict and never the raw
    # `req.assets`, so safety does not depend on the call order.
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
            # Include the `warning:` lines of tectonic itself. The TEX path
            # can read only the console stream.
            warnings=_collect_warnings(full_log),
            duration_s=perf_counter() - start,
        )
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


async def render_blob_async(req: BuildRequest) -> BuildResult:
    """Run `render_blob` off the event loop in an isolated context.

    The default executor runs the build under a copy of the current context.
    So the `_render_depth` `ContextVar`, and every later render-time context
    variable, stays private to this request. Concurrent async builds cannot
    corrupt the box-nesting depth of each other.

    Returns:
        The same `BuildResult` that `render_blob` returns.
    """
    loop = asyncio.get_running_loop()
    ctx = contextvars.copy_context()

    def _call() -> BuildResult:
        return ctx.run(render_blob, req)

    return await loop.run_in_executor(None, _call)


# A caller that builds its own limits can start from these default numbers.
DEFAULT_LIMITS: BuildLimits = BuildLimits()
