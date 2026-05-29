from dataclasses import dataclass
from typing import Protocol, override

from model.base_model import TeX


class SupportsStr(Protocol):
    @override
    def __str__(self) -> str: ...


@dataclass
class Raw(TeX):
    content: SupportsStr
    safe: bool = True

    @property
    @override
    def children(self) -> tuple["TeX", ...]:
        return tuple()

    @override
    def serialize(self) -> str:
        content = str(self.content)

        if self.safe and content.count("{") != content.count("}"):
            raise ValueError

        return content
