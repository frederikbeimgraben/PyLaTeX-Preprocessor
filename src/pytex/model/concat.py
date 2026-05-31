from dataclasses import dataclass
from typing import Final, override

from ..helpers.coerce import coerce_tex
from ..interface.tex import TeX


@dataclass(frozen=True, init=False)
class Concat(TeX):
    elements: Final[tuple[TeX]]

    def __init__(self, *elements: TeX | str) -> None:
        object.__setattr__(self, "elements", tuple(coerce_tex(e) for e in elements))

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return self.elements

    @property
    @override
    def rendered(self) -> str:
        return "".join(str(e) for e in self.elements)
