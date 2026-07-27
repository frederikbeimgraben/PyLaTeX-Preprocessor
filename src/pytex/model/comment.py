from dataclasses import dataclass, field
from typing import Final, override

from ..interface.tex import TeX
from ..registry import Registry

__all__ = ["Comment"]


@Registry.add
@dataclass(frozen=True)
class Comment(TeX):
    """A LaTeX comment: a `%`, then the text, then a newline.

    Attributes:
        text: Everything between the `%` and the end of the line. The leading
            space in `% note` is part of `text`.

    Note:
        The rendered output holds the trailing newline, so this node ends its
        own line.
    """

    text: Final[str]
    _parent: "TeX | None" = field(default=None, init=False, compare=False, repr=False)

    @property
    @override
    def rendered(self) -> str:
        return f"%{self.text}\n"
