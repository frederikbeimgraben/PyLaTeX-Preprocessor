from dataclasses import dataclass, field
from typing import override

from ...model.base_model import TeX
from ...model.group import Group
from ...model.raw import coerce_tex


@dataclass(init=False)
class BeginEnvironment(TeX):
    """``\\begin{name}[opts]{arg1}{arg2}...`` — bare environment opener.

    Use inside ``\\newenvironment`` begin/end bodies where you cannot use
    a full :class:`Environment` (the begin and end live in different
    branches of the definition).
    """

    name: str
    args: tuple[TeX, ...]
    options: str | None

    def __init__(
        self, name: str, *args: TeX | str, options: str | None = None
    ) -> None:
        self.name = name
        self.args = tuple(coerce_tex(a) for a in args)
        self.options = options

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return self.args

    @override
    def serialize(self) -> str:
        opt = f"[{self.options}]" if self.options is not None else ""
        body = "".join(f"{{{a.serialize()}}}" for a in self.args)
        return f"\\begin{{{self.name}}}{opt}{body}"


@dataclass
class EndEnvironment(TeX):
    """``\\end{name}`` — bare environment closer (companion to
    :class:`BeginEnvironment`)."""

    name: str
    _children: tuple[TeX, ...] = field(default_factory=tuple)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return f"\\end{{{self.name}}}"


@dataclass(init=False)
class Environment(TeX):
    """LaTeX environment wrapper (\\begin{name}...\\end{name})"""

    name: str
    body: TeX

    def __init__(self, name: str, body: TeX | str) -> None:
        self.name = name
        self.body = coerce_tex(body)

    @property
    @override
    def children(self) -> tuple["TeX", ...]:
        return (self.body,)

    @override
    def serialize(self, indent: int = 0) -> str:
        return self.serialize_indented(indent)

    def serialize_indented(self, indent: int) -> str:
        from ...model.serialization import serialize_with_indent

        indent_str = "  " * indent
        body_str = serialize_with_indent(self.body, indent + 1)

        body_lines = body_str.strip().split("\n")
        indented_body = "\n".join(
            ("  " * (indent + 1)) + line if line.strip() else line
            for line in body_lines
        )

        return (
            f"{indent_str}\\begin{{{self.name}}}\n"
            f"{indented_body}\n"
            f"{indent_str}\\end{{{self.name}}}"
        )


@dataclass(init=False)
class Item(TeX):
    """LaTeX \\item for lists"""

    content: TeX

    def __init__(self, content: TeX | str) -> None:
        self.content = coerce_tex(content)

    @property
    @override
    def children(self) -> tuple["TeX", ...]:
        return (self.content,)

    @override
    def serialize(self, indent: int = 0) -> str:
        return self.serialize_indented(indent)

    def serialize_indented(self, indent: int) -> str:
        from ...model.serialization import serialize_with_indent

        indent_str = "  " * indent
        content_str = serialize_with_indent(self.content, 0)
        return f"{indent_str}\\item {content_str}"


def Itemize(*items: TeX | str) -> Environment:
    """Create an itemize environment with items"""
    return Environment("itemize", Group(*items))


def Enumerate(*items: TeX | str) -> Environment:
    """Create an enumerate environment with items"""
    return Environment("enumerate", Group(*items))


def Quote(content: TeX | str) -> Environment:
    """Create a quote environment"""
    return Environment("quote", content)


def Verbatim(text: str) -> Environment:
    """Create a verbatim environment for code blocks"""
    from ...model.raw import Raw

    return Environment("verbatim", Raw(text, safe=False, escape_spaces=False))
