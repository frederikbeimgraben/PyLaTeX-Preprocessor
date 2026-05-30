"""Built-in LaTeX macros and commands.

This module provides strongly-typed wrappers for common LaTeX commands,
organized by category into submodules (text, sections, fontsizes, links,
utility, commands, lowlevel, packages).
"""

from .commands import (
    AtBeginDocument,
    AtEndDocument,
    Command,
    CounterWithin,
    CounterWithout,
    Crefname,
    DeclareRobustCommand,
    GlobalDef,
    Hypersetup,
    MakeAtLetter,
    NewCommand,
    NewCounter,
    NewEnvironment,
    NewLength,
    ProvideCommand,
    RenewCommand,
    SetCounter,
    SetLength,
)
from .fontsizes import (
    Huge,
    HugeHuge,
    Large,
    LargeLarge,
    LargeLargeLarge,
    Small,
    Tiny,
)
from .links import Href
from .lowlevel import (
    Apptocmd,
    AssignToks,
    AtBeginEnvironment,
    AtEndEnvironment,
    BeginAccSupp,
    Def,
    Ifdefstring,
    IfFontExistsTF,
    Ifnum,
    IfUndefined,
    ImmediateWrite,
    Let,
    NewToks,
    Pretocmd,
    RegisterAssign,
    Whiledo,
)
from .packages import BuiltinPackages
from .sections import (
    Paragraph,
    Section,
    Subparagraph,
    Subsection,
    Subsubsection,
)
from .text import (
    Bold,
    Emph,
    Italic,
    SmallCaps,
    Subscript,
    Superscript,
    Texttt,
    Underline,
)
from .utility import Newline, Relax

__all__ = [
    # Utility
    "Relax",
    "Newline",
    # Text formatting
    "Bold",
    "Italic",
    "Texttt",
    "Underline",
    "Emph",
    "SmallCaps",
    "Superscript",
    "Subscript",
    # Font sizes
    "Tiny",
    "Small",
    "Large",
    "LargeLarge",
    "LargeLargeLarge",
    "Huge",
    "HugeHuge",
    # Sections
    "Section",
    "Subsection",
    "Subsubsection",
    "Paragraph",
    "Subparagraph",
    # Links
    "Href",
    # Generic commands
    "Command",
    "NewCommand",
    "RenewCommand",
    "ProvideCommand",
    "DeclareRobustCommand",
    "NewLength",
    "SetLength",
    "NewCounter",
    "SetCounter",
    "CounterWithin",
    "CounterWithout",
    "AtBeginDocument",
    "AtEndDocument",
    "MakeAtLetter",
    "Hypersetup",
    "Crefname",
    "NewEnvironment",
    "GlobalDef",
    # Low-level primitives
    "Def",
    "Let",
    "NewToks",
    "AssignToks",
    "ImmediateWrite",
    "RegisterAssign",
    "Pretocmd",
    "Apptocmd",
    "AtBeginEnvironment",
    "AtEndEnvironment",
    "Whiledo",
    "IfFontExistsTF",
    "IfUndefined",
    "Ifnum",
    "Ifdefstring",
    "BeginAccSupp",
    # Package catalogue
    "BuiltinPackages",
]
