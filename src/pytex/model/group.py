from dataclasses import dataclass
from typing import override

from ..library.builtins import Relax
from .base_model import TeX
from .helpers import CLOSING_BRACE, OPENING_BRACE
from .raw import coerce_tex


@dataclass
class Group(TeX):
    _children: tuple[TeX, ...] = tuple()

    def __init__(self, *args: TeX | str) -> None:
        self._children = tuple(coerce_tex(a) for a in args)

    @property
    @override
    def children(self) -> tuple["TeX", ...]:
        return self._children

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
        from .serialization import serialize_with_indent

        # Groups don't add their own indentation, they just pass it through
        return (
            OPENING_BRACE
            + "".join(
                Relax.serialize() + serialize_with_indent(child, indent)
                for child in self.children
            )
            + CLOSING_BRACE
        )
