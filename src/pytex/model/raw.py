from typing import override

from pydantic.dataclasses import dataclass

from ..interface.tex import TeX


@dataclass
class Raw(TeX):
    content: str

    @property
    @override
    def rendered(self) -> str:
        return self.content
