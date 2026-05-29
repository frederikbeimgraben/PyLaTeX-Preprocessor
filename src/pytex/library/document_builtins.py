"""Document-level builtin macros for LaTeX.

Provides high-level commands that are typically used at the document level,
such as \\maketitle, \\tableofcontents, and \\newpage.
"""

from typing import ClassVar

from ..model.base_macro import BaseMacro


class _MakeTitle(BaseMacro):
    """The \\maketitle macro - generates the title block from \\title/\\author/\\date."""

    MACRO_ID: ClassVar[str] = "maketitle"


MakeTitle = _MakeTitle()


class _TableOfContents(BaseMacro):
    """The \\tableofcontents macro - generates a table of contents from headings."""

    MACRO_ID: ClassVar[str] = "tableofcontents"


TableOfContents = _TableOfContents()


class _NewPage(BaseMacro):
    """The \\newpage macro - forces a page break at the current position."""

    MACRO_ID: ClassVar[str] = "newpage"


NewPage = _NewPage()
