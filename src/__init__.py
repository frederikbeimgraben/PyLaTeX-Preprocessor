"""PyLaTeX - Type-safe LaTeX document generation with Python.

This is the main entry point that exports all user-facing classes and functions
for building LaTeX documents programmatically.

Example:
    from pylatex_experiment import Document, Section, Bold, Raw

    doc = Document(
        document_class="article",
        title="My Document",
        content=Section(Bold(Raw("Hello, World!")))
    )

    print(doc.serialize())
"""

# Core model types
# Text formatting and sections
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

# Document structure
from library.document import Document
from library.document_builtins import MakeTitle, NewPage, TableOfContents

# Environments
from library.environments import Enumerate, Environment, Item, Itemize, Quote, Verbatim

# File inclusion
from library.inclusion import Include, IncludeTeX, RawTeX

# Markdown support
from library.markdown import Markdown
from model.base_model import Package, TeX
from model.group import Group
from model.raw import Raw

__version__ = "0.1.0"

__all__ = [
    # Version
    "__version__",
    # Core types
    "TeX",
    "Package",
    "Raw",
    "Group",
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
