"""Built-in LaTeX macros and commands.

This module provides strongly-typed wrappers for common LaTeX commands,
organized by category.
"""

from library.builtins.text_and_sections import (
    Bold,
    Href,
    Italic,
    Newline,
    Paragraph,
    Relax,
    Section,
    Subparagraph,
    Subsection,
    Subsubsection,
    Texttt,
)

__all__ = [
    # Utility
    "Relax",
    "Newline",
    # Text formatting
    "Bold",
    "Italic",
    "Texttt",
    # Sections
    "Section",
    "Subsection",
    "Subsubsection",
    "Paragraph",
    "Subparagraph",
    # Links
    "Href",
]
