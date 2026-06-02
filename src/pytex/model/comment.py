from dataclasses import dataclass, field
from typing import Final, override

from ..interface.tex import TeX
from ..registry import Registry

__all__ = ["Comment"]


@Registry.add
@dataclass(frozen=True)
class Comment(TeX):
    """A LaTeX comment: ``%`` followed by text and the terminating newline.

    `text` is the content between the ``%`` and the end of the line (the
    leading space in ``% note`` is part of it). The trailing newline *is* part
    of the rendered output, so a comment ends its line as written.
    """

    text: Final[str]
    _parent: "TeX | None" = field(default=None, init=False, compare=False, repr=False)

    @property
    @override
    def rendered(self) -> str:
        return f"%{self.text}\n"
