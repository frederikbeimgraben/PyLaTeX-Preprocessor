from dataclasses import dataclass
from typing import Final, override

from ..helpers.coerce import coerce_tex
from ..helpers.parenting import attach
from ..interface.tex import TeX
from ..registry import Registry
from .empty import Empty, EmptyTeX
from .raw import Raw

__all__ = ["Concat"]


def _is_empty(node: TeX) -> bool:
    """A node that renders to nothing and can be dropped from a `Concat`."""
    return isinstance(node, EmptyTeX) or (isinstance(node, Raw) and node.content == "")


@Registry.add
@dataclass(frozen=True, init=False)
class Concat(TeX):
    elements: Final[tuple[TeX, ...]]

    def __new__(cls, *elements: TeX | str) -> TeX:
        coerced = tuple(
            node for node in map(coerce_tex, elements) if not _is_empty(node)
        )
        # Collapse trivial concatenations: nothing -> Empty, a single child ->
        # that child unwrapped. (`__init__` is a no-op, so returning a node of
        # any type here is safe.)
        if not coerced:
            return Empty
        if len(coerced) == 1:
            return coerced[0]
        instance = super().__new__(cls)
        object.__setattr__(instance, "elements", coerced)
        object.__setattr__(instance, "_parent", None)
        attach(instance, *coerced)
        return instance

    def __init__(self, *elements: TeX | str) -> None:
        # All construction happens in `__new__`; this keeps the call signature
        # and prevents dataclass from generating an `__init__` that would
        # overwrite the already-built instance.
        pass

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return self.elements

    @property
    @override
    def rendered(self) -> str:
        return "".join(str(e) for e in self.elements)
