"""KOMA-Script extension for PyTeX.

Builds on :mod:`pytex` to provide the KOMA-Script document classes
(``scrartcl`` / ``scrreprt`` / ``scrbook``) and the extra commands they add:
title-page metadata, font configuration, type-area control and the
``scrlayer-scrpage`` header/footer interface.

Example:
    from pytex import Group, Raw, Section
    from pytex_komascript import KomaDocument

    doc = KomaDocument(
        content=Group(Section(Raw("Intro")), Raw("Hello!")),
        title="Report",
        author="Jane Doe",
        font_size="11pt",
        paper_size="a4paper",
        div=12,
        headsepline=True,
        head_left="Report",
        head_right=Raw(r"\\pagemark", escape_spaces=False),
        foot_center=Raw(r"\\pagemark", escape_spaces=False),
    )
    print(doc.serialize())
"""

from .commands import (
    AddToKomaFont,
    Appendix,
    ArgCommand,
    BackMatter,
    CFoot,
    CHead,
    ClearPairOfPageStyles,
    Dedication,
    Extratitle,
    FrontMatter,
    IFoot,
    IHead,
    KomaOptions,
    MainMatter,
    OFoot,
    OHead,
    Pagestyle,
    Publishers,
    RecalcTypeArea,
    RedeclareSectionCommand,
    RedeclareSectionCommands,
    SetKomaFont,
    Subject,
    TitleHead,
)
from .document import DivValue, KomaClass, KomaDocument, ParSkip
from .model import Block

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "KomaDocument",
    "Block",
    "ArgCommand",
    # Type aliases
    "KomaClass",
    "ParSkip",
    "DivValue",
    # Title-page metadata
    "Subject",
    "Publishers",
    "TitleHead",
    "Dedication",
    "Extratitle",
    # Header / footer
    "IHead",
    "CHead",
    "OHead",
    "IFoot",
    "CFoot",
    "OFoot",
    "Pagestyle",
    "ClearPairOfPageStyles",
    # Fonts & options
    "SetKomaFont",
    "AddToKomaFont",
    "KomaOptions",
    "RecalcTypeArea",
    # Matter divisions
    "FrontMatter",
    "MainMatter",
    "BackMatter",
    "Appendix",
    # Sections
    "RedeclareSectionCommand",
    "RedeclareSectionCommands",
]
