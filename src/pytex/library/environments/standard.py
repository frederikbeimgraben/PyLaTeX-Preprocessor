from typing import override

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from ...model.base_model import TeX
from ...model.group import Group


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
    def serialize(self, indent: int = 0) -> str:
        r"""Serialize with optional indentation.

        Args:
            indent: Indentation level (default: 0)

        Returns:
            Serialized LaTeX string with proper indentation
        """
        return self.serialize_indented(indent)

    def serialize_indented(self, indent: int) -> str:
        r"""Serialize with indentation.

        Args:
            indent: Indentation level

        Returns:
            Serialized LaTeX string with proper indentation
        """
        from ...model.serialization import serialize_with_indent

        indent_str = "  " * indent
        body_str = serialize_with_indent(self.body, indent + 1)

        # Remove leading/trailing whitespace from body and indent it
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


@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class Item(TeX):
    """LaTeX \\item for lists"""

    content: TeX

    @property
    @override
    def children(self) -> tuple["TeX", ...]:
        return (self.content,)

    @override
    def serialize(self, indent: int = 0) -> str:
        """Serialize with optional indentation.

        Args:
            indent: Indentation level (default: 0)

        Returns:
            Serialized LaTeX string
        """
        return self.serialize_indented(indent)

    def serialize_indented(self, indent: int) -> str:
        """Serialize with indentation.

        Args:
            indent: Indentation level

        Returns:
            Serialized LaTeX string
        """
        from ...model.serialization import serialize_with_indent

        indent_str = "  " * indent
        content_str = serialize_with_indent(self.content, 0)
        return f"{indent_str}\\item {content_str}"


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
    from ...model.raw import Raw

    return Environment("verbatim", Raw(text, safe=False, escape_spaces=False))
