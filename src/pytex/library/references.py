"""LaTeX cross-references, citations, footnotes, and color commands."""

from dataclasses import dataclass
from typing import override

from ..model.base_model import Package, TeX
from ..model.raw import coerce_tex

# ============================================================================
# Cross-references
# ============================================================================


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


# ============================================================================
# Citations
# ============================================================================


@dataclass(init=False)
class Cite(TeX):
    """\\cite[note]{key1,key2,...}"""

    keys: tuple[str, ...]
    note: TeX | None

    def __init__(
        self, keys: "tuple[str, ...]", note: "TeX | str | None" = None
    ) -> None:
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


# ============================================================================
# Footnotes
# ============================================================================


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


# ============================================================================
# Color commands (require xcolor package)
# ============================================================================


@dataclass(init=False)
class TextColor(TeX):
    """\\textcolor{color}{content} — requires xcolor package."""

    color: str
    content: TeX

    def __init__(self, color: str, content: TeX | str) -> None:
        self.color = color
        self.content = coerce_tex(content)

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return {"xcolor"}

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.content,)

    @override
    def serialize(self) -> str:
        return f"\\textcolor{{{self.color}}}{{{self.content.serialize()}}}"


@dataclass(init=False)
class ColorBox(TeX):
    """\\colorbox{color}{content} — requires xcolor package."""

    color: str
    content: TeX

    def __init__(self, color: str, content: TeX | str) -> None:
        self.color = color
        self.content = coerce_tex(content)

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return {"xcolor"}

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.content,)

    @override
    def serialize(self) -> str:
        return f"\\colorbox{{{self.color}}}{{{self.content.serialize()}}}"


@dataclass(init=False)
class FBox(TeX):
    """\\fbox{content} — framed box."""

    content: TeX

    def __init__(self, content: TeX | str) -> None:
        self.content = coerce_tex(content)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.content,)

    @override
    def serialize(self) -> str:
        return f"\\fbox{{{self.content.serialize()}}}"
