"""Strongly-typed LaTeX builtin macros.

This module provides type-safe wrappers for common LaTeX commands.
Each macro is implemented as a dedicated class with proper type hints,
enabling IDE autocomplete and static type checking.
"""

from typing import override

from model.base_macro import BaseMacro
from model.base_model import TeX

# ============================================================================
# Utility Macros
# ============================================================================


class _Relax(BaseMacro):
    """The \\relax macro - does nothing, used as a no-op or separator."""

    @property
    @override
    def id(self) -> str:
        return "relax"

    @property
    @override
    def n_positional(self) -> int:
        return 0

    @property
    @override
    def keyword_args(self) -> dict[str, tuple[type[TeX], TeX]]:
        return {}


Relax = _Relax()


class _Newline(BaseMacro):
    """The \\\\ (newline/line break) macro."""

    @property
    @override
    def id(self) -> str:
        return "\\"

    @property
    @override
    def n_positional(self) -> int:
        return 0

    @property
    @override
    def keyword_args(self) -> dict[str, tuple[type[TeX], TeX]]:
        return {}


Newline = _Newline()


# ============================================================================
# Text Formatting Macros
# ============================================================================


class Bold(BaseMacro):
    """The \\textbf macro - renders text in bold.

    Args:
        content: The text content to render in bold.

    Example:
        Bold(Raw("important text"))
    """

    @property
    @override
    def id(self) -> str:
        return "textbf"

    @property
    @override
    def n_positional(self) -> int:
        return 1

    @property
    @override
    def keyword_args(self) -> dict[str, tuple[type[TeX], TeX]]:
        return {}


class Italic(BaseMacro):
    """The \\textit macro - renders text in italic.

    Args:
        content: The text content to render in italic.

    Example:
        Italic(Raw("emphasized text"))
    """

    @property
    @override
    def id(self) -> str:
        return "textit"

    @property
    @override
    def n_positional(self) -> int:
        return 1

    @property
    @override
    def keyword_args(self) -> dict[str, tuple[type[TeX], TeX]]:
        return {}


class Texttt(BaseMacro):
    """The \\texttt macro - renders text in monospace (typewriter) font.

    Args:
        content: The text content to render in monospace.

    Example:
        Texttt(Raw("code snippet"))
    """

    @property
    @override
    def id(self) -> str:
        return "texttt"

    @property
    @override
    def n_positional(self) -> int:
        return 1

    @property
    @override
    def keyword_args(self) -> dict[str, tuple[type[TeX], TeX]]:
        return {}


# ============================================================================
# Section Heading Macros
# ============================================================================


class Section(BaseMacro):
    """The \\section macro - top-level section heading.

    Args:
        title: The section title.

    Example:
        Section(Raw("Introduction"))
    """

    @property
    @override
    def id(self) -> str:
        return "section"

    @property
    @override
    def n_positional(self) -> int:
        return 1

    @property
    @override
    def keyword_args(self) -> dict[str, tuple[type[TeX], TeX]]:
        return {}


class Subsection(BaseMacro):
    """The \\subsection macro - second-level section heading.

    Args:
        title: The subsection title.

    Example:
        Subsection(Raw("Background"))
    """

    @property
    @override
    def id(self) -> str:
        return "subsection"

    @property
    @override
    def n_positional(self) -> int:
        return 1

    @property
    @override
    def keyword_args(self) -> dict[str, tuple[type[TeX], TeX]]:
        return {}


class Subsubsection(BaseMacro):
    """The \\subsubsection macro - third-level section heading.

    Args:
        title: The subsubsection title.

    Example:
        Subsubsection(Raw("Details"))
    """

    @property
    @override
    def id(self) -> str:
        return "subsubsection"

    @property
    @override
    def n_positional(self) -> int:
        return 1

    @property
    @override
    def keyword_args(self) -> dict[str, tuple[type[TeX], TeX]]:
        return {}


class Paragraph(BaseMacro):
    """The \\paragraph macro - fourth-level section heading.

    Args:
        title: The paragraph title.

    Example:
        Paragraph(Raw("Note"))
    """

    @property
    @override
    def id(self) -> str:
        return "paragraph"

    @property
    @override
    def n_positional(self) -> int:
        return 1

    @property
    @override
    def keyword_args(self) -> dict[str, tuple[type[TeX], TeX]]:
        return {}


class Subparagraph(BaseMacro):
    """The \\subparagraph macro - fifth-level section heading.

    Args:
        title: The subparagraph title.

    Example:
        Subparagraph(Raw("Remark"))
    """

    @property
    @override
    def id(self) -> str:
        return "subparagraph"

    @property
    @override
    def n_positional(self) -> int:
        return 1

    @property
    @override
    def keyword_args(self) -> dict[str, tuple[type[TeX], TeX]]:
        return {}


# ============================================================================
# Hyperlink Macro
# ============================================================================


class Href(BaseMacro):
    """The \\href macro - creates a hyperlink.

    Args:
        url: The URL target of the hyperlink.
        text: The visible link text.

    Example:
        Href(Raw("https://example.com"), Raw("Example Site"))

    Note:
        Requires the hyperref package in your LaTeX document.
    """

    @property
    @override
    def id(self) -> str:
        return "href"

    @property
    @override
    def n_positional(self) -> int:
        return 2

    @property
    @override
    def keyword_args(self) -> dict[str, tuple[type[TeX], TeX]]:
        return {}
