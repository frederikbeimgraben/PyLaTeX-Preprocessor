#!/usr/bin/env python3
"""Build .pytex files into LaTeX documents.

This script takes .pytex files (Python syntax TeX trees) and builds them
into .tex files, optionally compiling them to PDF.

Usage:
    python build_pytex.py input.pytex [output.tex] [--compile] [--indent]
    python build_pytex.py input.pytex --compile --indent

Options:
    --compile       Compile the .tex file to PDF using tectonic
    --indent        Use indented output for better readability
    -o, --output    Specify output .tex file (default: same name as input)
"""

import argparse
import subprocess
import sys
from pathlib import Path

from ..model.base_model import TeX


def load_pytex(pytex_path: Path):
    if not pytex_path.exists():
        raise FileNotFoundError(f"File not found: {pytex_path}")

    namespace: dict[str, object] = {"__builtins__": __builtins__}

    with open(pytex_path) as f:
        code = f.read()

    exec(code, namespace)

    from ..model.base_model import TeX

    for name in ["__pytex__", "document", "content", "root"]:
        obj = namespace.get(name)
        if isinstance(obj, TeX):
            return obj

    raise ValueError(
        f"No TeX object found in {pytex_path}. "
        + "Define `__pytex__ = Document(...)` in the file."
    )


def render_assets(node: TeX) -> None:
    """Render build-time assets (e.g. SVG -> PDF) across the tree."""
    from ..library.figures.svg import SVG

    if isinstance(node, SVG):
        node.render()
    for child in node.children:
        render_assets(child)


def build_pytex(
    pytex_path: Path, output_path: Path | None = None, indent: bool = False
):
    """Build a .pytex file to .tex.

    Args:
        pytex_path: Path to input .pytex file
        output_path: Path to output .tex file (default: same name as input)
        indent: Whether to use indented output

    Returns:
        Path to the generated .tex file
    """
    if output_path is None:
        output_path = pytex_path.with_suffix(".tex")

    print(f"Building {pytex_path} -> {output_path}")

    # Load the .pytex file
    tex_obj = load_pytex(pytex_path)

    # Create the build directory (relative to the invocation cwd) and render
    # any build-time assets (SVG -> PDF) into it before serialization.
    Path("build").mkdir(exist_ok=True)
    render_assets(tex_obj)

    # Serialize (with or without indentation)
    if indent:
        from ..model.serialization import serialize_with_indent

        tex_content = serialize_with_indent(tex_obj, indent=0)
    else:
        tex_content = tex_obj.serialize()

    # Write output
    with open(output_path, "w") as f:
        f.write(tex_content)

    print(f"✓ Generated {output_path}")
    return output_path


def compile_tex(tex_path: Path):
    """Compile a .tex file to PDF using tectonic.

    Args:
        tex_path: Path to .tex file

    Raises:
        RuntimeError: If compilation fails
    """
    print(f"Compiling {tex_path} to PDF...")

    try:
        subprocess.run(
            ["tectonic", str(tex_path)],
            capture_output=True,
            text=True,
            check=True,
        )
        pdf_path = tex_path.with_suffix(".pdf")
        print(f"✓ Generated {pdf_path}")
        return pdf_path
    except subprocess.CalledProcessError as e:
        print("✗ Compilation failed:", file=sys.stderr)
        print(e.stderr, file=sys.stderr)  # pyright: ignore[reportAny]
        raise RuntimeError(f"Failed to compile {tex_path}") from e
    except FileNotFoundError:
        print(
            "✗ tectonic not found. Please install tectonic to compile PDFs.",
            file=sys.stderr,
        )
        print("  See: https://tectonic-typesetting.github.io/", file=sys.stderr)
        raise


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Build .pytex files into LaTeX documents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("input", type=Path, help="Input .pytex file")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output .tex file (default: same name as input)",
    )
    parser.add_argument(
        "--compile",
        action="store_true",
        help="Compile to PDF using tectonic",
    )
    parser.add_argument(
        "--indent",
        action="store_true",
        help="Use indented output for better readability",
    )

    args = parser.parse_args()

    try:
        # Build .pytex -> .tex
        tex_path = build_pytex(
            args.input,  # pyright: ignore[reportAny]
            args.output,  # pyright: ignore[reportAny]
            args.indent,  # pyright: ignore[reportAny]
        )

        # Optionally compile to PDF
        if args.compile:  # pyright: ignore[reportAny]
            compile_tex(tex_path)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
