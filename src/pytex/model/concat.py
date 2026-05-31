from dataclasses import dataclass
from typing import Final, override

from ..helpers.coerce import coerce_tex
from ..helpers.parenting import attach
from ..interface.tex import TeX
from ..registry import Registry


@Registry.add
@dataclass(frozen=True, init=False)
class Concat(TeX):
    elements: Final[tuple[TeX]]

    def __init__(self, *elements: TeX | str) -> None:
        coerced = tuple(coerce_tex(e) for e in elements)
        object.__setattr__(self, "elements", coerced)
        object.__setattr__(self, "_parent", None)
        attach(self, *coerced)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return self.elements

    @property
    @override
    def rendered(self) -> str:
        return "".join(str(e) for e in self.elements)
