"""LaTeX float environments: figure and table."""

from dataclasses import dataclass
from typing import override

from ...model.base_model import TeX
from ...model.raw import coerce_tex


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
