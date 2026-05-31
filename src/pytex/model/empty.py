from typing import override

from pytex.interface.tex import TeX


class _Empty(TeX):
    @property
    @override
    def rendered(self) -> str:
        return ""


Empty = _Empty()
