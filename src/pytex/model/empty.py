from typing import override

from ..interface.tex import TeX


class EmptyTeX(TeX):
    @property
    @override
    def rendered(self) -> str:
        return ""


Empty = EmptyTeX()
