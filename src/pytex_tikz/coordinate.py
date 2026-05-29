"""TikZ coordinate primitives.

A :class:`Coordinate` is the value type passed to ``at (...)`` clauses and to
path operations. It supports Cartesian, polar, named-node, anchor and relative
forms; rendering returns the parenthesised TikZ literal so callers can drop it
straight into a path string.
"""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Coordinate:
    """A TikZ coordinate. ``serialize()`` returns the parenthesised literal."""

    spec: str

    def serialize(self) -> str:
        return f"({self.spec})"

    # ----- constructors ------------------------------------------------

    @classmethod
    def cartesian(cls, x: float | str, y: float | str) -> "Coordinate":
        """``(x, y)`` — Cartesian coordinate."""
        return cls(f"{x},{y}")

    @classmethod
    def polar(cls, angle: float | str, radius: float | str) -> "Coordinate":
        """``(angle:radius)`` — polar coordinate."""
        return cls(f"{angle}:{radius}")

    @classmethod
    def named(cls, name: str, anchor: str | None = None) -> "Coordinate":
        """``(name)`` or ``(name.anchor)`` — a previously declared node."""
        return cls(name if anchor is None else f"{name}.{anchor}")

    @classmethod
    def relative(
        cls,
        dx: float | str,
        dy: float | str,
        *,
        kind: Literal["+", "++"] = "++",
    ) -> "Coordinate":
        """``(+x, +y)`` (no last-point update) or ``(++x, ++y)`` (update)."""
        return cls(f"{kind}({dx},{dy})")

    @classmethod
    def page(cls, anchor: str = "center") -> "Coordinate":
        """``(current page.anchor)`` — current-page node anchor."""
        return cls(f"current page.{anchor}")
