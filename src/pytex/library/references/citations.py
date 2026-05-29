"""LaTeX citations: \\cite."""

from dataclasses import dataclass
from typing import override

from ...model.base_model import TeX
from ...model.raw import coerce_tex


@dataclass(init=False)
class Cite(TeX):
    """\\cite[note]{key1,key2,...}"""

    keys: tuple[str, ...]
    note: TeX | None

    def __init__(self, keys: "tuple[str, ...]", note: "TeX | str | None" = None) -> None:
        self.keys = keys
        self.note = coerce_tex(note) if note is not None else None

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.note,) if self.note is not None else ()

    @override
    def serialize(self) -> str:
        note_str = f"[{self.note.serialize()}]" if self.note is not None else ""
        return f"\\cite{note_str}{{{','.join(self.keys)}}}"


def cite(*keys: str, note: "TeX | str | None" = None) -> Cite:
    """Cite one or more bibliography keys. cite('key1', 'key2', note=Raw('p. 42'))"""
    return Cite(keys=keys, note=note)
