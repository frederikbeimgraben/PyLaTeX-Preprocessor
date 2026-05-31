from typing import Final, TypeVarTuple, Unpack, cast, override

from pydantic.dataclasses import dataclass

from pytex.interface.tex import TeX

C = TypeVarTuple("C")


@dataclass(frozen=True, init=False)
class Concat[*C](TeX):
    elements: Final[tuple[Unpack[C]]]

    def __init__(self, *elements: *C) -> None:
        object.__setattr__(self, "elements", elements)

    @property
    @override
    def rendered(self) -> str:
        return "\\relax ".join(cast(TeX, e).rendered for e in self.elements)
