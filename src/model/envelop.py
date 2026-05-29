from dataclasses import dataclass
from typing import override

from model.base_model import TeX


@dataclass
class Envelop(TeX):
    left: str | TeX
    child: TeX
    right: str | TeX | None = None

    @property
    @override
    def children(self) -> tuple["TeX", ...]:
        return (self.child,)

    @override
    def serialize(self) -> str:
        left = self.left
        right = self.right if self.right is not None else left

        return (
            left.serialize()
            if isinstance(left, TeX)
            else left + self.child.serialize() + right.serialize()
            if isinstance(right, TeX)
            else right
        )
