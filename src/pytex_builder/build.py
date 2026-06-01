"""``pytex`` command-line entry point.

Renders a ``.tex`` or ``.py`` input to a LaTeX file and, optionally, compiles
it with tectonic - running ``makeindex`` between passes so ``glossaries`` and
acronyms resolve.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, cast

from .console import Console
from .render import get_tex_node
from .tectonic import BuildError, ensure_tectonic, run_makeindex, run_tectonic

__all__ = ["Config", "main"]

if TYPE_CHECKING:
    from pytex_hsrtreport.document import HSRTReport

MAX_PASSES = 3


@dataclass(frozen=True)
class Config:
    input: Path
    output: Path
    build: bool
    build_dir: Path
    shell_escape: bool


def _default_output(inp: Path, build_dir: Path) -> Path:
    """Default rendered-output path inside the build directory.

    The driver extension is dropped, plus a trailing ``.tex`` if the source is
    named after its target (the ``name.tex.py`` convention). The result lives in
    ``build_dir`` so the ``.out.tex`` and its inline assets (fonts, logos,
    images) stay out of the source tree:

    * ``example.tex.py`` -> ``<build_dir>/example.out.tex``
    * ``report.py``      -> ``<build_dir>/report.out.tex``
    * ``paper.tex``      -> ``<build_dir>/paper.out.tex``
    """
    base = inp
    if base.suffix.lower() in {".py", ".tex"}:
        base = base.with_suffix("")
    if base.suffix.lower() == ".tex":
        base = base.with_suffix("")
    return build_dir / f"{base.name}.out.tex"


def _parse_args(argv: list[str]) -> Config:
    parser = argparse.ArgumentParser(
        prog="pytex",
        description="Render PyTeX (.py) or LaTeX (.tex) sources and build PDFs.",
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
    ns = parser.parse_args(argv)
    inp = cast("Path", ns.input)
    build_dir = cast("Path", ns.build_dir)
    return Config(
        input=inp,
        output=cast("Path | None", ns.output) or _default_output(inp, build_dir),
        build=cast("bool", ns.build),
        build_dir=build_dir,
        shell_escape=cast("bool", ns.shell_escape),
    )


def _run(cfg: Config, console: Console) -> None:
    if not cfg.input.exists():
        raise BuildError(f"input file does not exist: {cfg.input}")

    output = cfg.output
    build_dir = cfg.build_dir

    console.step(f"Rendering {cfg.input.name}")
    tex_node = get_tex_node(cfg.input)
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
