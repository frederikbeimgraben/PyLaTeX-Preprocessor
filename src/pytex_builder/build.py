"""``pytex`` command-line entry point.

Renders a ``.tex`` or ``.py`` input to a LaTeX file and, optionally, compiles
it with tectonic - running ``makeindex`` between passes so ``glossaries`` and
acronyms resolve.

Security / trust
----------------
The CLI runs in a **TRUSTED** context by default. It imports and executes
``.py`` inputs, evaluates ``.tex`` ``\\iffalse{pytex(...)}\\fi`` replacements
and Markdown ``eval`` comments, and enables tectonic shell-escape. That is
remote-code-execution *by design* and is safe only for documents **you wrote
yourself**. Never point the default CLI at a file from an untrusted source.

To render foreign or untrusted input, pass ``--untrusted`` (or
``--trust-level {sandboxed,untrusted}``). Those route the build through the
:mod:`pytex_api` trust policy, which disables every code-execution surface (no
Python exec, no ``.tex`` replacements, no Markdown eval), forces shell-escape
off, enforces the package allowlist, and applies resource limits - with
``sandboxed`` additionally requiring the Podman OS sandbox for PDF builds.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import TYPE_CHECKING, cast

from pytex_analyze import Optimize, Severity, analyze

# Import the trust enum from the value-type module, not the package root:
# `pytex_api/__init__` imports `pytex_builder.console`, so going through the
# root here would be a circular import. `_models` pulls only stdlib.
from pytex_api._models import TrustLevel

from .console import Console, color_enabled
from .render import get_tex_node
from .tectonic import BuildError, ensure_tectonic, run_makeindex, run_tectonic
from .tree import render_tree

__all__ = ["Config", "main"]

if TYPE_CHECKING:
    from pytex.interface.tex import TeX
    from pytex_api import InputKind
    from pytex_hsrtreport.document import HSRTReport

MAX_PASSES = 3


@dataclass(frozen=True)
class Config:
    input: Path
    output: Path
    build: bool
    build_dir: Path
    shell_escape: bool
    tree: bool = False
    force: bool = False
    variant: str | None = None
    config: dict[str, object] | None = None
    # TRUSTED (default) runs the in-process pipeline with full code-execution
    # power; any other level routes the build through the pytex_api trust policy.
    trust: TrustLevel = TrustLevel.TRUSTED


def _default_output(inp: Path, build_dir: Path) -> Path:
    """Default rendered-output path inside the build directory.

    The driver extension is dropped, plus a trailing ``.tex`` if the source is
    named after its target (the ``name.tex.py`` convention). The result lives in
    ``build_dir`` so the ``.out.tex`` and its inline assets (fonts, logos,
    images) stay out of the source tree:

    The stem is also slugified (whitespace and shell/TeX-hostile characters
    become ``_``) because it becomes the TeX ``\\jobname``; spaces there break
    tectonic's biber/makeindex steps (the ``.bcf`` path cannot be opened):

    * ``example.tex.py``        -> ``<build_dir>/example.out.tex``
    * ``report.py``             -> ``<build_dir>/report.out.tex``
    * ``2026-06-15 STUPA.md``   -> ``<build_dir>/2026-06-15_STUPA.md.out.tex``
    """
    base = inp
    if base.suffix.lower() in {".py", ".tex"}:
        base = base.with_suffix("")
    if base.suffix.lower() == ".tex":
        base = base.with_suffix("")
    return build_dir / f"{_slug(base.name)}.out.tex"


def _slug(name: str) -> str:
    """Make `name` safe as a TeX jobname: collapse whitespace and drop
    characters that confuse tectonic/biber/makeindex."""
    name = re.sub(r"\s+", "_", name.strip())
    name = re.sub(r"[^\w.\-]", "", name)
    return name or "document"


def _version() -> str:
    try:
        return version("pytex-preprocessor")
    except PackageNotFoundError:
        return "unknown"


def _parse_args(argv: list[str]) -> Config:
    parser = argparse.ArgumentParser(
        prog="pytex",
        description=(
            "Render PyTeX (.py) or LaTeX (.tex) sources and build PDFs. "
            "Runs in a TRUSTED context by default (executes .py inputs, .tex "
            "pytex() replacements, and shell-escape) - use only on your OWN "
            "documents; pass --untrusted for input from foreign sources."
        ),
    )
    _ = parser.add_argument(
        "--version", action="version", version=f"pytex {_version()}"
    )
    _ = parser.add_argument(
        "input",
        type=Path,
        help=(
            "input file: a .tex file (wrapped in IncludeTeX) or a .py file"
            + " exposing a '__pytex__' TeX node"
        ),
    )
    _ = parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="rendered .tex output path (default: <build-dir>/<input>.out.tex)",
    )
    _ = parser.add_argument(
        "-b",
        "--build",
        action="store_true",
        help="compile the rendered .tex to PDF with tectonic",
    )
    _ = parser.add_argument(
        "--build-dir",
        type=Path,
        default=Path("build"),
        help="directory for build artifacts and tectonic output (default: build)",
    )
    _ = parser.add_argument(
        "--no-shell-escape",
        dest="shell_escape",
        action="store_false",
        help=(
            "disable shell-escape (on by default for TRUSTED builds; needed for"
            + " inline images). Non-trusted builds force shell-escape off anyway"
        ),
    )
    trust_group = parser.add_mutually_exclusive_group()
    _ = trust_group.add_argument(
        "--trust-level",
        choices=[level.value for level in TrustLevel],
        default=TrustLevel.TRUSTED.value,
        metavar="LEVEL",
        help=(
            "how much to trust the input (default: trusted). 'trusted' runs the"
            + " full in-process pipeline (Python exec, .tex replacements,"
            + " shell-escape) - use only on your OWN documents. 'sandboxed' and"
            + " 'untrusted' route the build through the pytex_api trust policy:"
            + " no code/shell surface, package allowlist, resource limits"
            + " (sandboxed also requires the Podman OS sandbox for PDFs)"
        ),
    )
    _ = trust_group.add_argument(
        "--untrusted",
        dest="trust_level",
        action="store_const",
        const=TrustLevel.UNTRUSTED.value,
        help="shorthand for --trust-level untrusted; for foreign/untrusted input",
    )
    _ = parser.add_argument(
        "-t",
        "--tree",
        action="store_true",
        help="also print the TeX-node tree of the input before rendering",
    )
    _ = parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="skip the optimize+analysis pass and build even if problems are found",
    )
    _ = parser.add_argument(
        "--variant",
        default=None,
        metavar="STYLE",
        help=(
            "Markdown output style: plain, report, report-makers, "
            + "protocol-asta, protocol-stupa (default: auto-detect)"
        ),
    )
    _ = parser.add_argument(
        "--config",
        default=None,
        metavar="JSON",
        help="JSON object of document-class params, merged over the frontmatter",
    )
    ns = parser.parse_args(argv)
    inp = cast("Path", ns.input)
    build_dir = cast("Path", ns.build_dir)
    variant = cast("str | None", ns.variant)
    if variant is not None:
        from .variants import VARIANT_NAMES

        if variant not in VARIANT_NAMES:
            parser.error(f"--variant must be one of {', '.join(VARIANT_NAMES)}")
    config = _parse_config(cast("str | None", ns.config), parser)
    return Config(
        input=inp,
        output=cast("Path | None", ns.output) or _default_output(inp, build_dir),
        build=cast("bool", ns.build),
        build_dir=build_dir,
        shell_escape=cast("bool", ns.shell_escape),
        tree=cast("bool", ns.tree),
        force=cast("bool", ns.force),
        variant=variant,
        config=config,
        trust=TrustLevel(cast("str", ns.trust_level)),
    )


def _parse_config(
    raw: str | None, parser: argparse.ArgumentParser
) -> dict[str, object] | None:
    if raw is None:
        return None
    try:
        value = cast("object", json.loads(raw))
    except json.JSONDecodeError as exc:
        parser.error(f"--config is not valid JSON: {exc}")
    if not isinstance(value, dict):
        parser.error("--config must be a JSON object")
    return cast("dict[str, object]", value)


def _optimize(tex_node: TeX) -> TeX:
    """Return a render-equivalent, tidied version of the input tree.

    `Optimize` rewrites node trees but does not descend into document nodes, so
    for a `Document` (and its subclasses, e.g. `HSRTReport`) the body is
    optimised in place - keeping the document object, its type, and its
    inline-asset methods intact.
    """
    from pytex.model.document import Document

    if isinstance(tex_node, Document):
        tex_node.body = Optimize(tex_node.body)
        return tex_node
    return Optimize(tex_node)


def _analyze(tex_node: TeX, console: Console) -> None:
    """Run the static checks and report them; abort on any error-level issue.

    `--force` bypasses this entirely (the caller skips the call).
    """
    issues = analyze(tex_node)
    errors = 0
    for issue in issues:
        if issue.severity is Severity.ERROR:
            errors += 1
            console.error(issue.message)
        else:
            console.warn(issue.message)
    if errors:
        raise BuildError(
            f"analysis found {errors} problem(s); pass -f/--force to build anyway"
        )


def _input_kind_for(path: Path) -> InputKind:
    """Map a CLI input suffix to a declared :class:`pytex_api.InputKind`.

    ``.py``/``.tex.py`` -> ``TEX_PY`` (Python-executing, rejected by every
    non-TRUSTED policy), ``.tex`` -> ``TEX``, ``.md``/``.markdown`` ->
    ``MARKDOWN``. Unknown suffixes raise :class:`BuildError`, matching the
    trusted dispatcher in :mod:`pytex_builder.render`.
    """
    from pytex_api import InputKind

    suffix = path.suffix.lower()
    if suffix == ".py":
        return InputKind.TEX_PY
    if suffix == ".tex":
        return InputKind.TEX
    if suffix in (".md", ".markdown"):
        return InputKind.MARKDOWN
    raise BuildError(
        f"unsupported input type '{suffix or path.name}'; expected .tex, .py or .md"
    )


def _run_untrusted(cfg: Config, console: Console) -> None:
    """Render or build ``cfg.input`` through the :mod:`pytex_api` trust policy.

    Reads the source bytes and hands them to :func:`pytex_api.render_blob` under
    ``cfg.trust``, so the gating decisions (no Python exec, no ``.tex``
    replacements, no Markdown eval, shell-escape off, package allowlist,
    resource limits, and - for SANDBOXED - the Podman sandbox) are the API's,
    never duplicated here. Any :class:`pytex_api.ApiError` is mapped to a
    :class:`BuildError` so ``main`` reports it like every other build failure.

    ``--tree`` and the optimize/analysis pass are TRUSTED-only conveniences (they
    need the in-process node tree) and do not apply on this path.
    """
    from pytex_api import ApiError, BuildRequest, OutputKind, render_blob

    if cfg.tree:
        console.warn("--tree is unavailable for non-trusted builds; skipping")

    input_kind = _input_kind_for(cfg.input)
    output_kind = OutputKind.PDF if cfg.build else OutputKind.TEX
    request = BuildRequest(
        source=cfg.input.read_bytes(),
        input_kind=input_kind,
        output_kind=output_kind,
        trust=cfg.trust,
        variant=cfg.variant,
        config=cfg.config or {},
    )

    console.step(f"Rendering {cfg.input.name} ({cfg.trust.value})")
    try:
        result = render_blob(request)
    except ApiError as exc:
        raise BuildError(str(exc)) from exc

    for warning in result.warnings:
        console.warn(warning)

    if output_kind is OutputKind.TEX:
        cfg.output.parent.mkdir(parents=True, exist_ok=True)
        _ = cfg.output.write_bytes(result.output)
        console.detail(f"wrote {cfg.output} ({len(result.output):,} bytes)")
        return

    cfg.build_dir.mkdir(parents=True, exist_ok=True)
    pdf = cfg.build_dir / f"{cfg.output.stem}.pdf"
    _ = pdf.write_bytes(result.output)
    console.success(f"Built {pdf}")


def _run(cfg: Config, console: Console) -> None:
    if not cfg.input.exists():
        raise BuildError(f"input file does not exist: {cfg.input}")

    if cfg.trust is not TrustLevel.TRUSTED:
        _run_untrusted(cfg, console)
        return

    output = cfg.output
    build_dir = cfg.build_dir

    console.step(f"Rendering {cfg.input.name}")
    tex_node = get_tex_node(cfg.input, variant=cfg.variant, config=cfg.config)

    # Normalise then check, both skipped with --force. Optimize is
    # render-equivalent, so the output is unchanged; it just tidies the tree
    # (the printed --tree and the analysis below then see the clean version).
    if not cfg.force:
        tex_node = _optimize(tex_node)

    if cfg.tree:
        print(render_tree(tex_node, color=color_enabled(sys.stdout)))

    if not cfg.force:
        _analyze(tex_node, console)

    source = tex_node.rendered
    output.parent.mkdir(parents=True, exist_ok=True)
    _ = output.write_text(source)
    console.detail(f"wrote {output} ({len(source):,} bytes)")

    if not cfg.build:
        return

    build_dir.mkdir(parents=True, exist_ok=True)

    # Materialise inline assets (fonts, logos, images) alongside the .tex (in
    # the build dir by default) so the TeX engine can locate them by the
    # relative paths in the preamble.
    if hasattr(tex_node, "write_inline_fonts"):
        cast("HSRTReport", tex_node).write_inline_fonts(str(output.parent))
    if hasattr(tex_node, "write_inline_logos"):
        cast("HSRTReport", tex_node).write_inline_logos(str(output.parent))
    if hasattr(tex_node, "write_inline_images"):
        cast("HSRTReport", tex_node).write_inline_images(str(output.parent))

    binary = ensure_tectonic(console)

    job = output.stem
    for pass_no in range(1, MAX_PASSES + 1):
        console.step(f"Compiling (pass {pass_no})")
        run_tectonic(
            binary, output, build_dir, shell_escape=cfg.shell_escape, console=console
        )
        # Resolve glossaries after the first pass; rerun only if it changed.
        if pass_no == 1 and run_makeindex(job, build_dir, console=console):
            continue
        break

    pdf = build_dir / f"{job}.pdf"
    if pdf.exists():
        console.success(f"Built {pdf}")
    else:
        console.warn("tectonic reported success but produced no PDF")
        console.hint(f"check the log in {build_dir}")


def main(argv: list[str] | None = None) -> int:
    cfg = _parse_args(sys.argv[1:] if argv is None else argv)
    console = Console()
    try:
        _run(cfg, console)
    except BuildError as exc:
        head, *rest = str(exc).splitlines() or [""]
        console.error(head)
        for line in rest:
            console.detail(line)
        return 1
    except KeyboardInterrupt:
        console.error("interrupted")
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
