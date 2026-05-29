"""Document-level builtin macros for LaTeX.

Provides high-level commands that are typically used at the document level,
such as \\maketitle, \\tableofcontents, and \\newpage.
"""

from typing import override

from ..model.base_macro import BaseMacro
from ..model.base_model import TeX


class _MakeTitle(BaseMacro):
    """The \\maketitle macro - generates the title block.

    Renders the document title, author, and date based on metadata
    set via \\title{}, \\author{}, and \\date{} commands.

    Example:
        Group(
            Title(Raw("My Document")),
            Author(Raw("John Doe")),
            Date(Raw("2024-01-01")),
            MakeTitle,
            Raw("Document content...")
        )
    """

    @property
    @override
    def id(self) -> str:
        return "maketitle"

    @property
    @override
    def n_positional(self) -> int:
        return 0

    @property
    @override
    def keyword_args(self) -> dict[str, tuple[type[TeX], TeX]]:
        return {}


MakeTitle = _MakeTitle()


class _TableOfContents(BaseMacro):
    """The \\tableofcontents macro - generates table of contents.

    Automatically generates a table of contents based on section headings
    in the document.

    Example:
        Group(
            TableOfContents,
            Section(Raw("Introduction")),
            Raw("Content...")
        )
    """

    @property
    @override
    def id(self) -> str:
        return "tableofcontents"

    @property
    @override
    def n_positional(self) -> int:
        return 0

    @property
    @override
    def keyword_args(self) -> dict[str, tuple[type[TeX], TeX]]:
        return {}


TableOfContents = _TableOfContents()


class _NewPage(BaseMacro):
    """The \\newpage macro - starts a new page.

    Forces a page break at the current position in the document.

    Example:
        Group(
            Raw("Content on page 1..."),
            NewPage,
            Raw("Content on page 2...")
        )
    """

    @property
    @override
    def id(self) -> str:
        return "newpage"

    @property
    @override
    def n_positional(self) -> int:
        return 0

    @property
    @override
    def keyword_args(self) -> dict[str, tuple[type[TeX], TeX]]:
        return {}


NewPage = _NewPage()
