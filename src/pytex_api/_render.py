"""Trust-gated step from source bytes to rendered LaTeX.

This module holds the gates on the code-execution surfaces:

* the import of a `.tex.py` or `.py` file through `exec_module`, which only a
  `trusted` build may do,
* the Markdown `[//]: # "EXPR"` eval comments, which PyTeX strips for every
  non-trusted build,
* the inline `pytex(...)` markers in a `.tex` source, which PyTeX turns off
  for every non-trusted build.

PyTeX then checks the rendered LaTeX against the package allowlist before it
returns. So a forbidden `\\usepackage` fails whether the result is the
rendered `.tex` file or the input to a PDF compile.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from pytex.model.raw import Raw

from ._models import ApiError, InputKind, TrustError
from ._security import enforce_packages, strip_markdown_eval_comments

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from ._models import BuildRequest
    from ._policy import TrustPolicy

__all__ = ["render_to_latex"]

# The config keys that name logo files. A caller uploads a logo as a request
# asset and names it here by its plain file name.
_LOGO_KEYS: Final[tuple[str, ...]] = ("logos", "footer_logos")


def _workdir_logo(item: object, workdir: Path) -> object:
    """Point one logo entry at the request asset of that name.

    Returns:
        The absolute path of the asset in `workdir`, when the entry names a
        file that is there. Every other entry comes back unchanged, so a
        vendored logo name such as `INF` still selects the bundled logo.
    """
    if not isinstance(item, str):
        return item
    # `validate_asset_name` refuses a path separator, so a name that holds one
    # can never be an asset of this request. The check also keeps the joined
    # path inside the work directory.
    if "/" in item or "\\" in item:
        return item
    candidate = workdir / item
    return str(candidate) if candidate.is_file() else item


def _resolve_workdir_logos(
    config: Mapping[str, object], workdir: Path
) -> Mapping[str, object]:
    """Rewrite the logo config keys to the request assets in the work directory.

    A document build resolves a relative logo path against the current working
    directory of the process, which is not the work directory. So an uploaded
    logo needs an absolute path. This function replaces each entry of the
    `logos` and `footer_logos` keys that names a file in `workdir`. It touches
    no other key.

    Returns:
        The config itself when no entry needs a change, or a copy with the two
        logo keys rewritten.
    """
    patched: dict[str, object] = {}
    for key in _LOGO_KEYS:
        raw = config.get(key)
        if isinstance(raw, str):
            resolved: object = _workdir_logo(raw, workdir)
        elif isinstance(raw, list):
            resolved = [_workdir_logo(item, workdir) for item in raw]  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
        else:
            continue
        if resolved != raw:
            patched[key] = resolved
    return {**config, **patched} if patched else config


def _decode(source: bytes) -> str:
    try:
        return source.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ApiError(f"source is not valid UTF-8: {exc}") from exc


def _render_python_source(source: bytes, workdir: Path) -> str:
    # `get_tex_node` is the public entry point that dispatches on the suffix.
    # It imports a `.py` path and returns the `__pytex__` node of the module.
    # Only a `trusted` build reaches this function.
    from pytex_builder.render import get_tex_node

    text = _decode(source)
    path = workdir / "input.py"
    _ = path.write_text(text, encoding="utf-8")
    return get_tex_node(path).rendered


def _render_markdown_source(
    req: BuildRequest, policy: TrustPolicy, workdir: Path
) -> str:
    from pytex_builder.variants import build_document

    text = _decode(req.source)
    if not policy.allow_markdown_eval:
        text = strip_markdown_eval_comments(text)
    config = _resolve_workdir_logos(req.config, workdir)
    document = build_document(text, variant=req.variant, config=config)
    # The report variant and the protocol variants load bundled fonts through
    # the fontspec option `Path=fonts/...` (see `HSRTFontSetup`). PyTeX must
    # write those TTF files to disk in the temporary work directory, or XeTeX
    # fails with "the font ... cannot be found". A plain document has no
    # `write_inline_fonts` method and skips this step.
    write_inline_fonts = getattr(document, "write_inline_fonts", None)
    if callable(write_inline_fonts):
        write_inline_fonts(str(workdir))
    # The logos (converted from SVG to PDF) and the inline images need the
    # same treatment. The tikz title overlay and footer overlay name them by
    # the relative path `logos/<file>`, so the files must sit next to the
    # rendered `.tex` file. If not, tectonic fails with "Unable to load
    # picture or PDF file 'logos/...'". The step is best-effort. `inkscape`
    # converts an SVG logo. When inkscape is missing, for example during a
    # warm-up render, PyTeX logs the problem and continues instead of a failed
    # render. A PDF logo, which is the common case for a report or a meeting
    # protocol, needs no converter and still lands on disk. `OSError` covers a
    # missing inkscape binary, and `CalledProcessError` a conversion error.
    _materialise_best_effort(document, "write_inline_logos", workdir)
    _materialise_best_effort(document, "write_inline_images", workdir)
    return document.rendered


def _materialise_best_effort(document: object, method: str, workdir: Path) -> None:
    """Call `document.<method>(workdir)` if it exists, and log converter errors.

    A missing converter binary or a failed conversion must not fail the whole
    render, so this function logs the error and returns.
    """
    import logging
    import subprocess

    fn = getattr(document, method, None)
    if not callable(fn):
        return
    try:
        fn(str(workdir))
    except (OSError, subprocess.CalledProcessError) as exc:  # pragma: no cover - infra
        logging.getLogger("pytex_api").warning(
            "%s could not materialise assets (%s); continuing without them", method, exc
        )


def render_to_latex(req: BuildRequest, policy: TrustPolicy, workdir: Path) -> str:
    """Render the source of the request to a LaTeX string under the policy.

    Args:
        workdir: The temporary work directory of the request. The Python
            execution path is the only path that writes there, because it
            needs a real module file to import.

    Returns:
        The rendered LaTeX source, already checked against the package
        allowlist.

    Raises:
        TrustError: The input kind is `TEX_PY` and the policy blocks Python
            execution, or the rendered LaTeX requires a forbidden package.
        ApiError: The source is not valid UTF-8, or the input kind is unknown.
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
        # `Raw` gates the inline `pytex(...)` markers. An untrusted `.tex`
        # source keeps each `\iffalse` block as an inert literal, and PyTeX
        # never evaluates it.
        latex = Raw(
            _decode(req.source),
            allow_replacements=policy.allow_tex_replacements,
        ).rendered
    elif kind is InputKind.MARKDOWN:
        latex = _render_markdown_source(req, policy, workdir)
    else:  # pragma: no cover - exhaustive over InputKind
        raise ApiError(f"unsupported input kind: {kind}")

    enforce_packages(latex, policy)
    return latex
