"""Python-side replacement for ``\\foreach`` inside a tikzpicture.

The original ``\\foreach \\i in {1,...,N} { ... }`` is unrolled in Python so the
result is a flat sequence of TeX nodes — no TeX-level loop machinery is needed
and the produced statements are introspectable from Python.
"""

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import override

from pytex import TeX
from pytex_komascript.model import Block


def unroll(
    items: Iterable[object],
    build: Callable[[object], TeX],
) -> TeX:
    """Map ``build`` over ``items``; return the concatenation as a Block."""
    return Block(*(build(item) for item in items))


@dataclass(init=False)
class ForEach(TeX):
    """Convenience wrapper: ``ForEach(items, build)`` -> unrolled Block.

    ``build`` is a Python callable that receives one item per iteration and
    returns a TeX node.
    """

    block: TeX

    def __init__(
        self,
        items: Iterable[object],
        build: Callable[[object], TeX],
    ) -> None:
        self.block = unroll(items, build)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.block,)

    @override
    def serialize(self) -> str:
        return self.block.serialize()


__all__ = ["unroll", "ForEach"]
