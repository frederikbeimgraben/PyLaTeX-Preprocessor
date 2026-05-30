"""Container primitives used by the KOMA-Script layer."""

from dataclasses import dataclass
from typing import override

from pytex.model.base_model import TeX
from pytex.model.raw import coerce_tex


@dataclass(init=False)
class Concat(TeX):
    """Children serialised back-to-back with no separator.

    Use when sibling nodes must butt up against each other (an inline run
    of macro + literal text + macro, for instance).
    """

    _children: tuple[TeX, ...]

    def __init__(self, *parts: TeX | str) -> None:
        self._children = tuple(coerce_tex(p) for p in parts)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return self._children

    @override
    def serialize(self) -> str:
        return "".join(child.serialize() for child in self._children)


@dataclass(init=False)
class Block(TeX):
    """Newline-separated sequence of TeX nodes with no surrounding braces.

    Unlike :class:`pytex.Group`, ``Block`` does not wrap its children in
    ``{ ... }``; it simply emits each child on its own line. This makes it
    suitable for preamble command lists (``\\setkomafont{...}{...}`` etc.).
    Children remain visible to the tree walker, so packages required by the
    commands are still collected automatically.
    """

    _children: tuple[TeX, ...]

    def __init__(self, *parts: TeX | str) -> None:
        self._children = tuple(coerce_tex(p) for p in parts)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return self._children

    @override
    def serialize(self) -> str:
        # Newline-joined (no trailing newline) so the block fits cleanly inside
        # another LaTeX group — a trailing newline plus the closing brace would
        # show up as a blank line and trip TeX's paragraph detection inside
        # \AtBeginPage / \AtBeginDocument bodies.
        return "\n".join(child.serialize() for child in self._children)
