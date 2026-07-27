"""`pytex-tex2py`: convert a `.tex` file into a `.tex.py` file.

PyTeX reads the input file as one `Raw` node through `IncludeTeX`. The optimize
pass then turns it into a native node tree. That pass expands the inline
`pytex(...)` markers and recognizes comments and math. This module serializes
the node tree back to Python that rebuilds the same tree:

    __pytex__ = Concat(Comment(...), Raw("..."), ControlSequence("today", ()), ...)

When you run the result through `pytex`, it renders byte-for-byte what the
original `.tex` file rendered. A node that this module does not handle becomes
a literal `Raw` of its rendered output, so the conversion always round-trips.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import TYPE_CHECKING, cast

from pytex.helpers.with_package import WithPackage
from pytex.interface.tex import TeX
from pytex.model.comment import Comment
from pytex.model.concat import Concat
from pytex.model.control_sequence import ControlSequence, Parameter
from pytex.model.empty import EmptyTeX
from pytex.model.include import IncludeTeX
from pytex.model.raw import Raw
from pytex_analyze import Optimize

from .console import Console
from .tectonic import BuildError

if TYPE_CHECKING:
    from pytex.interface.control_sequence import Parameters, ParameterType

__all__ = ["main", "to_python"]


class _Serializer:
    """Builds the Python expression for a node and records the imports it needs."""

    def __init__(self) -> None:
        self.imports: set[tuple[str, str]] = set()

    def _need(self, module: str, name: str) -> None:
        self.imports.add((module, name))

    def _literal(self, node: TeX) -> str:
        """Return the rendered LaTeX of `node` as a literal `Raw` expression.

        This is the fallback for a node that `emit` does not handle.
        """
        self._need("pytex.model.raw", "Raw")
        return f"Raw({node.rendered!r}, allow_replacements=False)"

    def emit(self, node: TeX) -> str:
        if isinstance(node, Concat):
            self._need("pytex.model.concat", "Concat")
            return f"Concat({', '.join(self.emit(e) for e in node.elements)})"
        if isinstance(node, Comment):
            self._need("pytex.model.comment", "Comment")
            return f"Comment({node.text!r})"
        if isinstance(node, Raw):
            if node.namespace is not None:
                return self._literal(node)
            self._need("pytex.model.raw", "Raw")
            if node.allow_replacements:
                return f"Raw({node.content!r})"
            return f"Raw({node.content!r}, allow_replacements=False)"
        if isinstance(node, Parameter):
            self._need("pytex.model.control_sequence", "Parameter")
            value = cast("Parameter[ParameterType]", node).value
            rendered = self.emit(value) if isinstance(value, TeX) else repr(value)
            return (
                f"Parameter({rendered}, optional=True)"
                if node.optional
                else f"Parameter({rendered})"
            )
        if isinstance(node, ControlSequence):
            self._need("pytex.model.control_sequence", "ControlSequence")
            cs = cast("ControlSequence[Parameters]", node)
            # This drops `required_packages`, which does not change what the
            # control sequence renders.
            return f"ControlSequence({cs.name!r}, {self._tuple(cs.params)})"
        if isinstance(node, WithPackage):
            self._need("pytex.helpers.with_package", "WithPackage")
            package = cast("object", node.package)
            name = getattr(package, "name", package)
            return f"WithPackage({self.emit(cast('TeX', node.child))}, {name!r})"
        if isinstance(node, EmptyTeX):
            self._need("pytex.model.empty", "Empty")
            return "Empty"
        return self._literal(node)

    def _tuple(self, items: Parameters) -> str:
        parts = [self.emit(item) for item in (items or ())]
        if len(parts) == 1:
            return f"({parts[0]},)"
        return f"({', '.join(parts)})"

    def import_block(self) -> str:
        by_module: dict[str, set[str]] = {}
        for module, name in self.imports:
            by_module.setdefault(module, set()).add(name)
        return "\n".join(
            f"from {module} import {', '.join(sorted(names))}"
            for module, names in sorted(by_module.items())
        )


def to_python(node: TeX) -> str:
    """Return a complete `.tex.py` source that rebuilds `node`."""
    serializer = _Serializer()
    expr = serializer.emit(node)  # records every import the tree needs
    if isinstance(node, Concat) and node.elements:
        # One element per line keeps a whole-document `Concat` readable.
        body = ",\n    ".join(serializer.emit(e) for e in node.elements)
        expr = f"Concat(\n    {body},\n)"
    return f"{serializer.import_block()}\n\n__pytex__ = {expr}\n"


def _output_path(inp: Path) -> Path:
    name = inp.name
    for suffix in (".tex", ".py"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return inp.with_name(f"{name}.tex.py")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pytex-tex2py",
        description="Convert a .tex file into an equivalent .tex.py source.",
    )
    _ = parser.add_argument("input", type=Path, help="the .tex file to convert")
    _ = parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="output .tex.py path (default: <input>.tex.py)",
    )
    ns = parser.parse_args(argv)
    inp = cast("Path", ns.input)
    output = cast("Path | None", ns.output) or _output_path(inp)
    console = Console()
    try:
        if not inp.exists():
            raise BuildError(f"input file does not exist: {inp}")
        console.step(f"Converting {inp.name}")
        node = Optimize(IncludeTeX(inp))
        source = to_python(node)
        output.parent.mkdir(parents=True, exist_ok=True)
        _ = output.write_text(source)
        console.success(f"Wrote {output} ({len(source):,} bytes)")
    except BuildError as exc:
        console.error(str(exc))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
