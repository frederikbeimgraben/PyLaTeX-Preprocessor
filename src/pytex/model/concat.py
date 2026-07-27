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
    """Report whether the node renders to nothing, so `Concat` can drop it."""
    return isinstance(node, EmptyTeX) or (isinstance(node, Raw) and node.content == "")


@Registry.add
@dataclass(frozen=True, init=False)
class Concat(TeX):
    """Child nodes that render one after the other, with no separator.

    `Concat` drops every `EmptyTeX` child and every `Raw` child with empty
    content. It then collapses the trivial cases. With no child left it returns
    `Empty`. With one child left it returns that child unwrapped. So a
    `Concat(...)` call can return a node that is not a `Concat`.
    """

    elements: Final[tuple[TeX, ...]]

    def __new__(cls, *elements: TeX | str) -> TeX:
        coerced = tuple(
            node for node in map(coerce_tex, elements) if not _is_empty(node)
        )
        # Collapse the trivial cases: no child -> Empty, one child -> that
        # child unwrapped. Python calls `__init__` only when `__new__` returns
        # a `Concat`, and `__init__` does nothing, so a node of any type is
        # safe to return here.
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
        # `__new__` builds the instance. This method only holds the call
        # signature. It also stops the dataclass decorator from generating an
        # `__init__` that would overwrite the instance that `__new__` built.
        pass

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return self.elements

    @property
    @override
    def rendered(self) -> str:
        return "".join(str(e) for e in self.elements)
