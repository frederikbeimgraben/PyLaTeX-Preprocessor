"""LaTeX footnotes: \\footnote."""

from dataclasses import dataclass
from typing import override

from ...model.base_model import TeX
from ...model.raw import coerce_tex


@dataclass(init=False)
class Footnote(TeX):
    """\\footnote{content}"""

    content: TeX

    def __init__(self, content: TeX | str) -> None:
        self.content = coerce_tex(content)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.content,)

    @override
    def serialize(self) -> str:
        return f"\\footnote{{{self.content.serialize()}}}"
