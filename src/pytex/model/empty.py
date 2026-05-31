from typing import override

from ..interface.tex import TeX
from ..registry import Registry


@Registry.add
class EmptyTeX(TeX):
    @property
    @override
    def rendered(self) -> str:
        return ""


Empty = EmptyTeX()
