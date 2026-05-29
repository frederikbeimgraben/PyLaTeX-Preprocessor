"""Built-in LaTeX macros and commands.

This module provides strongly-typed wrappers for common LaTeX commands,
organized by category into submodules (text, sections, fontsizes, links,
utility).
"""

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
]
