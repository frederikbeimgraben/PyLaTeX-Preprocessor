from dataclasses import dataclass
from typing import Protocol, override

from .base_model import TeX


class SupportsStr(Protocol):
    @override
    def __str__(self) -> str: ...


@dataclass
class Raw(TeX):
    content: SupportsStr
    safe: bool = False
    escape_spaces: bool = True
    namespace: dict[str, object] | None = None

    @property
    @override
    def children(self) -> tuple["TeX", ...]:
        return tuple()

    @override
    def serialize(self, indent: int = 0) -> str:
        """Serialize with optional indentation.

        Raw content is not indented.

        Args:
            indent: Indentation level (ignored)

        Returns:
            Serialized string
        """
        return self.serialize_indented(indent)

    def serialize_indented(self, _indent: int) -> str:
        """Serialize with indentation.

        Raw content is not indented.

        Args:
            indent: Indentation level (ignored)

        Returns:
            Serialized string
        """
        from .escapes import evaluate_escapes

        content = evaluate_escapes(
            str(self.content), self.namespace, self.escape_spaces
        )

        if self.safe and content.count("{") != content.count("}"):
            raise ValueError

        return content


def coerce_tex(x: TeX | str) -> "TeX":
    if isinstance(x, str):
        return Raw(x)
    return x
