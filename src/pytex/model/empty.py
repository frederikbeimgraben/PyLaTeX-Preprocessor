from typing import override

from ..interface.tex import TeX
from ..registry import Registry

__all__ = ["EmptyTeX"]


@Registry.add
class EmptyTeX(TeX):
    """A node that renders to an empty string.

    Use the module-level `Empty` instance instead of a new one. `Concat` drops
    every `EmptyTeX` child.
    """

    _parent: "TeX | None" = None

    @property
    @override
    def rendered(self) -> str:
        return ""


Empty = EmptyTeX()
