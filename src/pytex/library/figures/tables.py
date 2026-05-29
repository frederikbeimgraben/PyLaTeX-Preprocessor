"""LaTeX tabular content: rows, horizontal rules, and the tabular environment."""

from dataclasses import dataclass
from typing import override

from ...model.base_model import TeX
from ...model.raw import coerce_tex


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
