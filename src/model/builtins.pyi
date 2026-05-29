"""Type stubs for strongly-typed LaTeX builtin macros.

Provides explicit type hints for IDE autocomplete and static type checking.
"""

from typing import override

from model.base_macro import BaseMacro
from model.base_model import TeX

# ============================================================================
# Utility Macros
# ============================================================================

class _Relax(BaseMacro):
    """The \\relax macro - does nothing, used as a no-op or separator."""

    def __init__(self) -> None: ...
    @property
    @override
    def id(self) -> str: ...
    @property
    @override
    def n_positional(self) -> int: ...
    @property
    @override
    def keyword_args(self) -> dict[str, tuple[type[TeX], TeX]]: ...

Relax: _Relax

class _Newline(BaseMacro):
    """The \\\\ (newline/line break) macro."""

    def __init__(self) -> None: ...
    @property
    @override
    def id(self) -> str: ...
    @property
    @override
    def n_positional(self) -> int: ...
    @property
    @override
    def keyword_args(self) -> dict[str, tuple[type[TeX], TeX]]: ...

Newline: _Newline

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

    def __init__(self, content: TeX) -> None: ...
    @property
    @override
    def id(self) -> str: ...
    @property
    @override
    def n_positional(self) -> int: ...
    @property
    @override
    def keyword_args(self) -> dict[str, tuple[type[TeX], TeX]]: ...

class Italic(BaseMacro):
    """The \\textit macro - renders text in italic.

    Args:
        content: The text content to render in italic.

    Example:
        Italic(Raw("emphasized text"))
    """

    def __init__(self, content: TeX) -> None: ...
    @property
    @override
    def id(self) -> str: ...
    @property
    @override
    def n_positional(self) -> int: ...
    @property
    @override
    def keyword_args(self) -> dict[str, tuple[type[TeX], TeX]]: ...

class Texttt(BaseMacro):
    """The \\texttt macro - renders text in monospace (typewriter) font.

    Args:
        content: The text content to render in monospace.

    Example:
        Texttt(Raw("code snippet"))
    """

    def __init__(self, content: TeX) -> None: ...
    @property
    @override
    def id(self) -> str: ...
    @property
    @override
    def n_positional(self) -> int: ...
    @property
    @override
    def keyword_args(self) -> dict[str, tuple[type[TeX], TeX]]: ...

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

    def __init__(self, title: TeX) -> None: ...
    @property
    @override
    def id(self) -> str: ...
    @property
    @override
    def n_positional(self) -> int: ...
    @property
    @override
    def keyword_args(self) -> dict[str, tuple[type[TeX], TeX]]: ...

class Subsection(BaseMacro):
    """The \\subsection macro - second-level section heading.

    Args:
        title: The subsection title.

    Example:
        Subsection(Raw("Background"))
    """

    def __init__(self, title: TeX) -> None: ...
    @property
    @override
    def id(self) -> str: ...
    @property
    @override
    def n_positional(self) -> int: ...
    @property
    @override
    def keyword_args(self) -> dict[str, tuple[type[TeX], TeX]]: ...

class Subsubsection(BaseMacro):
    """The \\subsubsection macro - third-level section heading.

    Args:
        title: The subsubsection title.

    Example:
        Subsubsection(Raw("Details"))
    """

    def __init__(self, title: TeX) -> None: ...
    @property
    @override
    def id(self) -> str: ...
    @property
    @override
    def n_positional(self) -> int: ...
    @property
    @override
    def keyword_args(self) -> dict[str, tuple[type[TeX], TeX]]: ...

class Paragraph(BaseMacro):
    """The \\paragraph macro - fourth-level section heading.

    Args:
        title: The paragraph title.

    Example:
        Paragraph(Raw("Note"))
    """

    def __init__(self, title: TeX) -> None: ...
    @property
    @override
    def id(self) -> str: ...
    @property
    @override
    def n_positional(self) -> int: ...
    @property
    @override
    def keyword_args(self) -> dict[str, tuple[type[TeX], TeX]]: ...

class Subparagraph(BaseMacro):
    """The \\subparagraph macro - fifth-level section heading.

    Args:
        title: The subparagraph title.

    Example:
        Subparagraph(Raw("Remark"))
    """

    def __init__(self, title: TeX) -> None: ...
    @property
    @override
    def id(self) -> str: ...
    @property
    @override
    def n_positional(self) -> int: ...
    @property
    @override
    def keyword_args(self) -> dict[str, tuple[type[TeX], TeX]]: ...

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

    def __init__(self, url: TeX, text: TeX) -> None: ...
    @property
    @override
    def id(self) -> str: ...
    @property
    @override
    def n_positional(self) -> int: ...
    @property
    @override
    def keyword_args(self) -> dict[str, tuple[type[TeX], TeX]]: ...
