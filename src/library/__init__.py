"""High-level LaTeX document building library.

This module provides convenient abstractions for building complete LaTeX documents,
including document structure, package management, and file inclusion.
"""

from library.builtins import (
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
from library.document import Document
from library.document_builtins import MakeTitle, NewPage, TableOfContents
from library.environments import Enumerate, Environment, Item, Itemize, Quote, Verbatim
from library.inclusion import Include, IncludeTeX, RawTeX
from library.markdown import Markdown

__all__ = [
    # Document structure
    "Document",
    "MakeTitle",
    "TableOfContents",
    "NewPage",
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
    # Links and utilities
    "Href",
    "Newline",
    "Relax",
    # Environments
    "Environment",
    "Item",
    "Itemize",
    "Enumerate",
    "Quote",
    "Verbatim",
    # File inclusion
    "Include",
    "IncludeTeX",
    "RawTeX",
    # Markdown
    "Markdown",
]
