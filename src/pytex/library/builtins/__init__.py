"""Built-in LaTeX macros and commands.

This module provides strongly-typed wrappers for common LaTeX commands,
organized by category.
"""

from .text_and_sections import (
    Bold,
    Emph,
    Href,
    Huge,
    HugeHuge,
    Italic,
    Large,
    LargeLarge,
    LargeLargeLarge,
    Newline,
    Paragraph,
    Relax,
    Section,
    Small,
    SmallCaps,
    Subparagraph,
    Subscript,
    Subsection,
    Subsubsection,
    Superscript,
    Texttt,
    Tiny,
    Underline,
)

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
