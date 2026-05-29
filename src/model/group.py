from dataclasses import dataclass
from typing import override

from model.base_model import TeX
from model.builtins import Relax
from model.helpers import CLOSING_BRACE, OPENING_BRACE


@dataclass
class Group(TeX):
    _children: tuple[TeX, ...] = tuple()

    def __init__(self, *args: TeX) -> None:
        self._children = args

    @property
    @override
    def children(self) -> tuple["TeX", ...]:
        return self._children

    @override
    def serialize(self) -> str:
        return (
            OPENING_BRACE
            + "".join(Relax.serialize() + child.serialize() for child in self.children)
            + CLOSING_BRACE
        )
