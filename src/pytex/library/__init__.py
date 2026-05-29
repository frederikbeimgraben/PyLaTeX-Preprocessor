"""High-level LaTeX document building library.

This module provides convenient abstractions for building complete LaTeX documents,
including document structure, package management, and file inclusion.
"""

from .builtins import (
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
from .document import Document
from .document_builtins import MakeTitle, NewPage, TableOfContents
from .environments import Enumerate, Environment, Item, Itemize, Quote, Verbatim
from .figures import (
    Figure,
    HLine,
    IncludeGraphics,
    Row,
    Table,
    Tabular,
    tabular,
)
from .inclusion import Include, IncludeTeX, RawTeX
from .markdown import Markdown
from .math import (
    Align,
    AlignStar,
    DisplayMath,
    Equation,
    EquationStar,
    Gather,
    InlineMath,
)
from .references import (
    Cite,
    ColorBox,
    FBox,
    Footnote,
    Label,
    PageRef,
    Ref,
    TextColor,
    cite,
)

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
    # Math
    "InlineMath",
    "DisplayMath",
    "Equation",
    "EquationStar",
    "Align",
    "AlignStar",
    "Gather",
    # Figures & tables
    "IncludeGraphics",
    "Figure",
    "Table",
    "Tabular",
    "tabular",
    "Row",
    "HLine",
    # References, citations, footnotes
    "Label",
    "Ref",
    "PageRef",
    "Cite",
    "cite",
    "Footnote",
    # Colors & boxes
    "TextColor",
    "ColorBox",
    "FBox",
    # File inclusion
    "Include",
    "IncludeTeX",
    "RawTeX",
    # Markdown
    "Markdown",
]
