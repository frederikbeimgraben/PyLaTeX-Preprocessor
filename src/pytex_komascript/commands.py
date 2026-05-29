"""KOMA-Script specific LaTeX commands.

Strongly-typed wrappers for the commands KOMA-Script document classes
(``scrartcl``, ``scrreprt``, ``scrbook``) add on top of standard LaTeX:
title metadata, font configuration, type-area recalculation and the
``scrlayer-scrpage`` header/footer commands.
"""

from dataclasses import dataclass
from typing import ClassVar, override

from pytex.model.base_model import Package, TeX
from pytex.model.raw import coerce_tex

#: Package providing the modern KOMA header/footer interface.
SCRLAYER_SCRPAGE = "scrlayer-scrpage"


@dataclass(init=False)
class ArgCommand(TeX):
    """Base for ``\\command{content}`` style KOMA commands.

    Subclass and set the ``COMMAND`` class attribute (and optionally
    ``REQUIRES``) to define a new single-argument command.
    """

    COMMAND: ClassVar[str] = ""
    REQUIRES: ClassVar[frozenset[str]] = frozenset()

    content: TeX

    def __init__(self, content: TeX | str) -> None:
        self.content = coerce_tex(content)

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return set(self.REQUIRES)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.content,)

    @override
    def serialize(self) -> str:
        return f"\\{self.COMMAND}{{{self.content.serialize()}}}"


# ============================================================================
# Title-page metadata (preamble commands, like \title / \author)
# ============================================================================


class Subject(ArgCommand):
    """\\subject{...} — subject line above the title on the title page."""

    COMMAND: ClassVar[str] = "subject"


class Publishers(ArgCommand):
    """\\publishers{...} — publisher line below the author on the title page."""

    COMMAND: ClassVar[str] = "publishers"


class TitleHead(ArgCommand):
    """\\titlehead{...} — full-width head above the title."""

    COMMAND: ClassVar[str] = "titlehead"


class Dedication(ArgCommand):
    """\\dedication{...} — dedication page (\\maketitle renders it)."""

    COMMAND: ClassVar[str] = "dedication"


class Extratitle(ArgCommand):
    """\\extratitle{...} — half-title printed before the main title page."""

    COMMAND: ClassVar[str] = "extratitle"


# ============================================================================
# Header / footer commands (require scrlayer-scrpage)
# ============================================================================


class IHead(ArgCommand):
    """\\ihead{...} — inner header field."""

    COMMAND: ClassVar[str] = "ihead"
    REQUIRES: ClassVar[frozenset[str]] = frozenset({SCRLAYER_SCRPAGE})


class CHead(ArgCommand):
    """\\chead{...} — center header field."""

    COMMAND: ClassVar[str] = "chead"
    REQUIRES: ClassVar[frozenset[str]] = frozenset({SCRLAYER_SCRPAGE})


class OHead(ArgCommand):
    """\\ohead{...} — outer header field."""

    COMMAND: ClassVar[str] = "ohead"
    REQUIRES: ClassVar[frozenset[str]] = frozenset({SCRLAYER_SCRPAGE})


class IFoot(ArgCommand):
    """\\ifoot{...} — inner footer field."""

    COMMAND: ClassVar[str] = "ifoot"
    REQUIRES: ClassVar[frozenset[str]] = frozenset({SCRLAYER_SCRPAGE})


class CFoot(ArgCommand):
    """\\cfoot{...} — center footer field."""

    COMMAND: ClassVar[str] = "cfoot"
    REQUIRES: ClassVar[frozenset[str]] = frozenset({SCRLAYER_SCRPAGE})


class OFoot(ArgCommand):
    """\\ofoot{...} — outer footer field."""

    COMMAND: ClassVar[str] = "ofoot"
    REQUIRES: ClassVar[frozenset[str]] = frozenset({SCRLAYER_SCRPAGE})


@dataclass
class Pagestyle(TeX):
    """\\pagestyle{name} — select a page style (e.g. ``scrheadings``)."""

    name: str

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return f"\\pagestyle{{{self.name}}}"


@dataclass
class ClearPairOfPageStyles(TeX):
    """\\clearpairofpagestyles — reset all header/footer fields (scrlayer-scrpage)."""

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return {SCRLAYER_SCRPAGE}

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return "\\clearpairofpagestyles"


# ============================================================================
# Font configuration & type area
# ============================================================================


@dataclass
class SetKomaFont(TeX):
    """\\setkomafont{element}{commands} — replace the font of a KOMA element."""

    element: str
    commands: str

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return f"\\setkomafont{{{self.element}}}{{{self.commands}}}"


@dataclass
class AddToKomaFont(TeX):
    """\\addtokomafont{element}{commands} — append to the font of a KOMA element."""

    element: str
    commands: str

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return f"\\addtokomafont{{{self.element}}}{{{self.commands}}}"


@dataclass
class KomaOptions(TeX):
    """\\KOMAoptions{key=value,...} — change KOMA options after \\documentclass."""

    options: str

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return f"\\KOMAoptions{{{self.options}}}"


@dataclass
class RecalcTypeArea(TeX):
    """\\recalctypearea — recompute the type area after font/option changes."""

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return "\\recalctypearea"


# ============================================================================
# Matter divisions (scrbook / scrreprt)
# ============================================================================


@dataclass
class _BareCommand(TeX):
    """A no-argument control sequence, e.g. ``\\frontmatter``."""

    COMMAND: ClassVar[str] = ""

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return f"\\{self.COMMAND}"


class _FrontMatter(_BareCommand):
    COMMAND: ClassVar[str] = "frontmatter"


class _MainMatter(_BareCommand):
    COMMAND: ClassVar[str] = "mainmatter"


class _BackMatter(_BareCommand):
    COMMAND: ClassVar[str] = "backmatter"


class _Appendix(_BareCommand):
    COMMAND: ClassVar[str] = "appendix"


FrontMatter = _FrontMatter()
MainMatter = _MainMatter()
BackMatter = _BackMatter()
Appendix = _Appendix()


# ============================================================================
# Section-style redefinitions
# ============================================================================


@dataclass(init=False)
class RedeclareSectionCommand(TeX):
    """\\RedeclareSectionCommand[opt=val,...]{name} — KOMA section override."""

    name: str
    options: str

    def __init__(self, name: str, options: str) -> None:
        self.name = name
        self.options = options

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return f"\\RedeclareSectionCommand[{self.options}]{{{self.name}}}"


@dataclass(init=False)
class RedeclareSectionCommands(TeX):
    """\\RedeclareSectionCommands[opt=val,...]{name1,name2,...}."""

    names: tuple[str, ...]
    options: str

    def __init__(self, names: "tuple[str, ...] | list[str]", options: str) -> None:
        self.names = tuple(names)
        self.options = options

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        return (
            f"\\RedeclareSectionCommands[{self.options}]"
            f"{{{','.join(self.names)}}}"
        )
