from dataclasses import dataclass
from typing import Final, TypeVarTuple, Unpack, override

from ..interface.tex import TeX

C = TypeVarTuple("C")


@dataclass(frozen=True, init=False)
class Concat[*C](TeX):
    elements: Final[tuple[Unpack[C]]]

    def __init__(self, *elements: *C) -> None:
        object.__setattr__(self, "elements", elements)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return tuple(e for e in self.elements if isinstance(e, TeX))

    @property
    @override
    def rendered(self) -> str:
        return "".join(str(e) for e in self.elements)
