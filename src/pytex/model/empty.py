from typing import override

from ..interface.tex import TeX


class _Empty(TeX):
    @property
    @override
    def rendered(self) -> str:
        return ""


Empty = _Empty()
