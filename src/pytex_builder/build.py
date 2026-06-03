"""``pytex`` command-line entry point.

Renders a ``.tex`` or ``.py`` input to a LaTeX file and, optionally, compiles
it with tectonic - running ``makeindex`` between passes so ``glossaries`` and
acronyms resolve.
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

from .console import Console, color_enabled
from .render import get_tex_node
from .tectonic import BuildError, ensure_tectonic, run_makeindex, run_tectonic
from .tree import render_tree

__all__ = ["Config", "main"]

if TYPE_CHECKING:
    from pytex.interface.tex import TeX
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
        description="Render PyTeX (.py) or LaTeX (.tex) sources and build PDFs.",
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
        help="disable shell-escape (on by default; needed for inline images)",
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


def _run(cfg: Config, console: Console) -> None:
    if not cfg.input.exists():
        raise BuildError(f"input file does not exist: {cfg.input}")

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
