"""LaTeX figures, tables, and graphics support."""

from dataclasses import dataclass
from typing import override

from ..model.base_model import Package, TeX
from ..model.raw import coerce_tex

# ============================================================================
# Graphics
# ============================================================================


@dataclass
class IncludeGraphics(TeX):
    """\\includegraphics[options]{path} — requires graphicx package."""

    path: str
    width: str | None = None
    height: str | None = None
    scale: float | None = None
    angle: float | None = None

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return {"graphicx"}

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        opts: list[str] = []
        if self.width is not None:
            opts.append(f"width={self.width}")
        if self.height is not None:
            opts.append(f"height={self.height}")
        if self.scale is not None:
            opts.append(f"scale={self.scale}")
        if self.angle is not None:
            opts.append(f"angle={self.angle}")
        opt_str = f"[{','.join(opts)}]" if opts else ""
        return f"\\includegraphics{opt_str}{{{self.path}}}"


# ============================================================================
# Figure float
# ============================================================================


@dataclass(init=False)
class Figure(TeX):
    """figure float environment."""

    content: TeX
    caption: TeX | None
    label: str | None
    position: str
    centered: bool

    def __init__(
        self,
        content: TeX | str,
        caption: "TeX | str | None" = None,
        label: "str | None" = None,
        position: str = "htbp",
        centered: bool = True,
    ) -> None:
        self.content = coerce_tex(content)
        self.caption = coerce_tex(caption) if caption is not None else None
        self.label = label
        self.position = position
        self.centered = centered

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        kids: list[TeX] = [self.content]
        if self.caption is not None:
            kids.append(self.caption)
        return tuple(kids)

    @override
    def serialize(self) -> str:
        lines = [f"\\begin{{figure}}[{self.position}]"]
        if self.centered:
            lines.append("  \\centering")
        lines.append(f"  {self.content.serialize()}")
        if self.caption is not None:
            lines.append(f"  \\caption{{{self.caption.serialize()}}}")
        if self.label is not None:
            lines.append(f"  \\label{{{self.label}}}")
        lines.append("\\end{figure}")
        return "\n".join(lines)


# ============================================================================
# Tables
# ============================================================================


@dataclass
class _HLine(TeX):
    """\\hline — horizontal rule in a table."""

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return "\\hline"


HLine = _HLine()


@dataclass(init=False)
class _Row(TeX):
    cells: tuple[TeX, ...]

    def __init__(self, *cells: TeX | str) -> None:
        self.cells = tuple(coerce_tex(c) for c in cells)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return self.cells

    @override
    def serialize(self) -> str:
        return " & ".join(c.serialize() for c in self.cells) + " \\\\"


def Row(*cells: TeX | str) -> _Row:
    """A table row: Row(cell1, cell2, ...) → cell1 & cell2 \\\\"""
    return _Row(*cells)


@dataclass
class Tabular(TeX):
    """\\begin{tabular}{cols} rows \\end{tabular}"""

    columns: str
    rows: tuple[_Row | _HLine, ...]

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return self.rows

    @override
    def serialize(self) -> str:
        rows_str = "\n  ".join(r.serialize() for r in self.rows)
        return f"\\begin{{tabular}}{{{self.columns}}}\n  {rows_str}\n\\end{{tabular}}"


def tabular(columns: str, *rows: "_Row | _HLine") -> Tabular:
    """Create a Tabular. tabular('l|c|r', Row(...), HLine, Row(...))"""
    return Tabular(columns=columns, rows=rows)


@dataclass(init=False)
class Table(TeX):
    """table float environment."""

    content: TeX
    caption: TeX | None
    label: str | None
    position: str
    centered: bool

    def __init__(
        self,
        content: TeX | str,
        caption: "TeX | str | None" = None,
        label: "str | None" = None,
        position: str = "htbp",
        centered: bool = True,
    ) -> None:
        self.content = coerce_tex(content)
        self.caption = coerce_tex(caption) if caption is not None else None
        self.label = label
        self.position = position
        self.centered = centered

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        kids: list[TeX] = [self.content]
        if self.caption is not None:
            kids.append(self.caption)
        return tuple(kids)

    @override
    def serialize(self) -> str:
        lines = [f"\\begin{{table}}[{self.position}]"]
        if self.centered:
            lines.append("  \\centering")
        lines.append(f"  {self.content.serialize()}")
        if self.caption is not None:
            lines.append(f"  \\caption{{{self.caption.serialize()}}}")
        if self.label is not None:
            lines.append(f"  \\label{{{self.label}}}")
        lines.append("\\end{table}")
        return "\n".join(lines)
