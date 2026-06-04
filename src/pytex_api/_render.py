"""Trust-gated source-bytes -> rendered-LaTeX step.

This is where the code-execution surfaces are gated:

* ``.tex.py`` / ``.py`` import (``exec_module``) - TRUSTED only,
* Markdown ``[//]: # "EXPR"`` eval comments - stripped unless TRUSTED,
* ``.tex`` ``\\iffalse{pytex(...)}\\fi`` replacements - disabled unless TRUSTED.

The rendered LaTeX is then screened against the package allowlist before it is
returned, so a forbidden ``\\usepackage`` is caught whether the output is the
``.tex`` itself or the input to a PDF compile.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pytex.model.raw import Raw

from ._models import ApiError, InputKind, TrustError
from ._security import enforce_packages, strip_markdown_eval_comments

if TYPE_CHECKING:
    from pathlib import Path

    from ._models import BuildRequest
    from ._policy import TrustPolicy

__all__ = ["render_to_latex"]


def _decode(source: bytes) -> str:
    try:
        return source.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ApiError(f"source is not valid UTF-8: {exc}") from exc


def _render_python_source(source: bytes, workdir: Path) -> str:
    # The public, suffix-dispatching entry point: a `.py` path is imported and
    # its `__pytex__` node returned. Only reached on the TRUSTED path.
    from pytex_builder.render import get_tex_node

    text = _decode(source)
    path = workdir / "input.py"
    _ = path.write_text(text, encoding="utf-8")
    return get_tex_node(path).rendered


def _render_markdown_source(req: BuildRequest, policy: TrustPolicy) -> str:
    from pytex_builder.variants import build_document

    text = _decode(req.source)
    if not policy.allow_markdown_eval:
        text = strip_markdown_eval_comments(text)
    return build_document(text, variant=req.variant, config=req.config).rendered


def render_to_latex(req: BuildRequest, policy: TrustPolicy, workdir: Path) -> str:
    """Render the request's source to a LaTeX string under the trust policy.

    ``workdir`` is the per-request temp directory; it is only touched for the
    Python-execution path (which needs a real module file to import).
    """
    kind = req.input_kind
    if kind is InputKind.TEX_PY:
        if not policy.allow_python_exec:
            raise TrustError(
                "Python-executing input (.tex.py / .py) is only allowed for "
                + f"TRUSTED builds, not {policy.level.value}"
            )
        latex = _render_python_source(req.source, workdir)
    elif kind is InputKind.TEX:
        # Raw with replacements gated: untrusted .tex keeps `\iffalse pytex()`
        # blocks as inert literals instead of evaluating them.
        latex = Raw(
            _decode(req.source),
            allow_replacements=policy.allow_tex_replacements,
        ).rendered
    elif kind is InputKind.MARKDOWN:
        latex = _render_markdown_source(req, policy)
    else:  # pragma: no cover - exhaustive over InputKind
        raise ApiError(f"unsupported input kind: {kind}")

    enforce_packages(latex, policy)
    return latex
