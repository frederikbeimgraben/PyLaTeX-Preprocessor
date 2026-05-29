from typing import override

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from model.base_model import TeX
from model.group import Group


@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class Environment(TeX):
    """LaTeX environment wrapper (\\begin{name}...\\end{name})"""

    name: str
    body: TeX

    @property
    @override
    def children(self) -> tuple["TeX", ...]:
        return (self.body,)

    @override
    def serialize(self) -> str:
        return f"\\begin{{{self.name}}}\n{self.body.serialize()}\n\\end{{{self.name}}}"


@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class Item(TeX):
    """LaTeX \\item for lists"""

    content: TeX

    @property
    @override
    def children(self) -> tuple["TeX", ...]:
        return (self.content,)

    @override
    def serialize(self) -> str:
        return f"\\item {self.content.serialize()}"


def Itemize(*items: TeX) -> Environment:
    """Create an itemize environment with items"""
    return Environment("itemize", Group(*items))


def Enumerate(*items: TeX) -> Environment:
    """Create an enumerate environment with items"""
    return Environment("enumerate", Group(*items))


def Quote(content: TeX) -> Environment:
    """Create a quote environment"""
    return Environment("quote", content)


def Verbatim(text: str) -> Environment:
    """Create a verbatim environment for code blocks"""
    from model.raw import Raw

    return Environment("verbatim", Raw(text, safe=False))
