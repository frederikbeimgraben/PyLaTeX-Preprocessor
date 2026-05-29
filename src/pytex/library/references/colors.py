"""LaTeX color and box commands: \\textcolor, \\colorbox, \\fbox."""

from dataclasses import dataclass
from typing import override

from ...model.base_model import Package, TeX
from ...model.raw import coerce_tex


@dataclass(init=False)
class TextColor(TeX):
    """\\textcolor{color}{content} — requires xcolor package."""

    color: str
    content: TeX

    def __init__(self, color: str, content: TeX | str) -> None:
        self.color = color
        self.content = coerce_tex(content)

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return {"xcolor"}

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.content,)

    @override
    def serialize(self) -> str:
        return f"\\textcolor{{{self.color}}}{{{self.content.serialize()}}}"


@dataclass(init=False)
class ColorBox(TeX):
    """\\colorbox{color}{content} — requires xcolor package."""

    color: str
    content: TeX

    def __init__(self, color: str, content: TeX | str) -> None:
        self.color = color
        self.content = coerce_tex(content)

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return {"xcolor"}

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.content,)

    @override
    def serialize(self) -> str:
        return f"\\colorbox{{{self.color}}}{{{self.content.serialize()}}}"


@dataclass(init=False)
class FBox(TeX):
    """\\fbox{content} — framed box."""

    content: TeX

    def __init__(self, content: TeX | str) -> None:
        self.content = coerce_tex(content)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.content,)

    @override
    def serialize(self) -> str:
        return f"\\fbox{{{self.content.serialize()}}}"
