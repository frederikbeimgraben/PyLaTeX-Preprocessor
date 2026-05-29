"""LaTeX cross-references: \\label, \\ref, \\pageref."""

from dataclasses import dataclass
from typing import override

from ...model.base_model import TeX


@dataclass
class Label(TeX):
    """\\label{key}"""

    key: str

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return f"\\label{{{self.key}}}"


@dataclass
class Ref(TeX):
    """\\ref{key}"""

    key: str

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return f"\\ref{{{self.key}}}"


@dataclass
class PageRef(TeX):
    """\\pageref{key}"""

    key: str

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return f"\\pageref{{{self.key}}}"
