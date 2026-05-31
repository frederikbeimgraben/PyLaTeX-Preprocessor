from dataclasses import dataclass
from typing import override

from ..interface.tex import TeX


@dataclass
class Raw(TeX):
    content: str

    @property
    @override
    def rendered(self) -> str:
        return self.content
