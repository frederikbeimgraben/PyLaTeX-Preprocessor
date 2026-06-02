from dataclasses import dataclass, field
from typing import Final, override

from ..interface.tex import TeX
from ..registry import Registry

__all__ = ["Comment"]


@Registry.add
@dataclass(frozen=True)
class Comment(TeX):
    """A LaTeX comment: ``%`` followed by text up to the end of the line.

    `text` is everything after the ``%`` (the leading space in ``% note`` is
    part of it). The trailing newline is not included, so the comment composes
    with surrounding nodes exactly as written.
    """

    text: Final[str]
    _parent: "TeX | None" = field(default=None, init=False, compare=False, repr=False)

    @property
    @override
    def rendered(self) -> str:
        return f"%{self.text}"
