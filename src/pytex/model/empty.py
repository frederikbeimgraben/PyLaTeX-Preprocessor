from typing import override

from ..interface.tex import TeX
from ..registry import Registry

__all__ = ["EmptyTeX"]


@Registry.add
class EmptyTeX(TeX):
    _parent: "TeX | None" = None

    @property
    @override
    def rendered(self) -> str:
        return ""


Empty = EmptyTeX()
