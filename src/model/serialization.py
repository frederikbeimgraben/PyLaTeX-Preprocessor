"""Serialization utilities with indentation support.

Provides utilities for pretty-printing LaTeX output with proper indentation.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class Indentable(Protocol):
    """Protocol for objects that support indented serialization."""

    def serialize_indented(self, indent: int) -> str:
        """Serialize with indentation level.

        Args:
            indent: Number of indentation levels (each level = 2 spaces)

        Returns:
            Serialized string with appropriate indentation
        """
        ...


def indent_lines(text: str, indent: int) -> str:
    """Add indentation to each line of text.

    Args:
        text: Text to indent
        indent: Number of indentation levels (each level = 2 spaces)

    Returns:
        Indented text
    """
    if indent == 0:
        return text

    indent_str = "  " * indent
    lines = text.split("\n")
    return "\n".join(indent_str + line if line.strip() else line for line in lines)


@runtime_checkable
class Serializable(Protocol):
    """Protocol for objects with a serialize method (no indent parameter)."""

    def serialize(self) -> str: ...


def serialize_with_indent(obj: Indentable | Serializable, indent: int = 0) -> str:
    """Serialize an object with indentation if it supports it.

    Args:
        obj: Object to serialize (must have serialize method)
        indent: Indentation level

    Returns:
        Serialized string
    """
    if isinstance(obj, Indentable):
        return obj.serialize_indented(indent)
    else:
        return obj.serialize()
