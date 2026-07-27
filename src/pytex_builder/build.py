"""The command-line entry point of `pytex`.

This module renders an input file to a rendered `.tex` file. With `--build` it
also compiles that file to PDF with tectonic. It runs the makeindex step
between the compile passes, so that `glossaries` and acronyms resolve.

Note:
    The command runs at trust level `trusted` by default. At that level PyTeX
    imports and executes a `.tex.py` input file. It also evaluates the inline
    `pytex(...)` markers of a `.tex` input file, evaluates Markdown `eval`
    comments, and turns shell-escape on. This is code execution by design. Use
    the default only on documents you wrote yourself.

    If the input file comes from a source you do not trust, pass `--untrusted`
    or `--trust-level sandboxed`. Both options route the build through the
    `pytex_api` trust policy. The trust policy closes every code-execution
    surface, forces shell-escape off, applies the package allowlist, and
    applies resource limits. The value `sandboxed` also needs the Podman
    sandbox for a PDF build.
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

# Import the trust enum from the value-type module, not from the package root.
# `pytex_api/__init__` imports `pytex_builder.console`, so an import through the
# root would be circular. `_models` imports only the standard library.
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
    # The trust level `trusted` (the default) runs the in-process build with
    # every code-execution surface open. Every other trust level routes the
    # build through the `pytex_api` trust policy.
    trust: TrustLevel = TrustLevel.TRUSTED


def _default_output(inp: Path, build_dir: Path) -> Path:
    """Return the default path of the rendered `.tex` file.

    The path is inside the build directory, so the rendered `.tex` file and its
    inline assets stay out of the source tree. The inline assets are the fonts,
    the logos and the images. PyTeX drops the extension of the input file. It
    drops a second `.tex` extension when the input file follows the
    `name.tex.py` convention.

    The stem becomes the TeX `\\jobname`, so `_slug` cleans it. A space in the
    `\\jobname` breaks tectonic's biber step and makeindex step, because they
    cannot open the `.bcf` path.

    Example:
        `example.tex.py` -> `<build_dir>/example.out.tex`

        `report.py` -> `<build_dir>/report.out.tex`

        `2026-06-15 STUPA.md` -> `<build_dir>/2026-06-15_STUPA.md.out.tex`
    """
    base = inp
    if base.suffix.lower() in {".py", ".tex"}:
        base = base.with_suffix("")
    if base.suffix.lower() == ".tex":
        base = base.with_suffix("")
    return build_dir / f"{_slug(base.name)}.out.tex"


def _slug(name: str) -> str:
    """Make `name` safe as a TeX jobname.

    This function replaces each run of whitespace with `_`. It then removes
    every character that confuses tectonic, biber or makeindex.

    Returns:
        The safe name. When no character survives, the result is `document`.
    """
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
    """Run the optimize pass and return the tidied node tree.

    The optimize pass is render-equivalent. `Optimize` rewrites a node tree but
    does not descend into a document node. For a `Document`, and for a subclass
    such as `HSRTReport`, this function optimizes the body in place. The
    document node keeps its type and its inline-asset methods.
    """
    from pytex.model.document import Document

    if isinstance(tex_node, Document):
        tex_node.body = Optimize(tex_node.body)
        return tex_node
    return Optimize(tex_node)


def _analyze(tex_node: TeX, console: Console) -> None:
    """Run the analysis pass and print every issue it finds.

    `--force` skips the analysis pass. The caller then does not call this
    function at all.

    Raises:
        BuildError: The analysis pass reported at least one error-level issue.
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
    """Map the suffix of an input file to a declared `InputKind`.

    The mapping is `.py` and `.tex.py` -> `TEX_PY`, `.tex` -> `TEX`, and `.md`
    and `.markdown` -> `MARKDOWN`. The kind `TEX_PY` executes Python, so the
    trust policy rejects it at every trust level except `trusted`.

    Raises:
        BuildError: PyTeX does not support this suffix. The trusted dispatcher
            in `pytex_builder.render` raises the same error.
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
    """Render or build `cfg.input` through the `pytex_api` trust policy.

    This function reads the source bytes and passes them to
    `pytex_api.render_blob` at trust level `cfg.trust`. The trust policy makes
    every gating decision. It closes every code-execution surface, forces
    shell-escape off, applies the package allowlist, and applies resource
    limits. At trust level `sandboxed` it also uses the Podman sandbox. This
    module never repeats those decisions.

    `--tree`, the optimize pass and the analysis pass need the in-process node
    tree, so they work only at trust level `trusted`. This path ignores them.

    Raises:
        BuildError: `pytex_api` raised an `ApiError`. This function maps that
            error, so that `main` reports it like every other build failure.
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

    # `--force` skips the optimize pass and the analysis pass below. The
    # optimize pass is render-equivalent, so the rendered `.tex` file stays the
    # same. It only tidies the node tree, and `--tree` and the analysis pass
    # then see the tidied tree.
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

    # Write the inline assets to disk next to the rendered `.tex` file. The
    # inline assets are the fonts, the logos and the images. That directory is
    # the build directory by default, so the relative paths in the preamble
    # resolve during the compile pass.
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
        # Run the makeindex step after the first compile pass. Run a second
        # compile pass only when the makeindex step rebuilt an index.
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
