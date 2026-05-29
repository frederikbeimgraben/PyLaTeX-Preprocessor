"""Strongly-typed LaTeX builtin macros.

This module provides type-safe wrappers for common LaTeX commands.
Each macro is a dedicated class declaring its LaTeX command id and arity via
``MACRO_ID`` / ``N_POSITIONAL`` class attributes (see ``BaseMacro``). The
typed constructor signatures live in the accompanying ``.pyi`` stub.
"""

from typing import ClassVar, Protocol, override

from ...model.base_macro import BaseMacro

# ============================================================================
# Utility Macros
# ============================================================================


class _Relax(BaseMacro):
    """The \\relax macro - does nothing, used as a no-op or separator."""

    MACRO_ID: ClassVar[str] = "relax"


Relax = _Relax()


class _Newline(BaseMacro):
    """The \\\\ (newline/line break) macro."""

    MACRO_ID: ClassVar[str] = "\\"


Newline = _Newline()


# ============================================================================
# Text Formatting Macros
# ============================================================================


class Bold(BaseMacro):
    """The \\textbf macro - renders text in bold.

    Example:
        Bold(Raw("important text"))
    """

    MACRO_ID: ClassVar[str] = "textbf"
    N_POSITIONAL: ClassVar[int] = 1


class Italic(BaseMacro):
    """The \\textit macro - renders text in italic.

    Example:
        Italic(Raw("emphasized text"))
    """

    MACRO_ID: ClassVar[str] = "textit"
    N_POSITIONAL: ClassVar[int] = 1


class Texttt(BaseMacro):
    """The \\texttt macro - renders text in monospace (typewriter) font.

    Example:
        Texttt(Raw("code snippet"))
    """

    MACRO_ID: ClassVar[str] = "texttt"
    N_POSITIONAL: ClassVar[int] = 1


class Underline(BaseMacro):
    """The \\underline macro - underlines text."""

    MACRO_ID: ClassVar[str] = "underline"
    N_POSITIONAL: ClassVar[int] = 1


class Emph(BaseMacro):
    """The \\emph macro - semantic emphasis."""

    MACRO_ID: ClassVar[str] = "emph"
    N_POSITIONAL: ClassVar[int] = 1


class SmallCaps(BaseMacro):
    """The \\textsc macro - small capitals."""

    MACRO_ID: ClassVar[str] = "textsc"
    N_POSITIONAL: ClassVar[int] = 1


class Superscript(BaseMacro):
    """The \\textsuperscript macro."""

    MACRO_ID: ClassVar[str] = "textsuperscript"
    N_POSITIONAL: ClassVar[int] = 1


class Subscript(BaseMacro):
    """The \\textsubscript macro."""

    MACRO_ID: ClassVar[str] = "textsubscript"
    N_POSITIONAL: ClassVar[int] = 1


# ============================================================================
# Section Heading Macros
# ============================================================================


class Section(BaseMacro):
    """The \\section macro - top-level section heading.

    Example:
        Section(Raw("Introduction"))
    """

    MACRO_ID: ClassVar[str] = "section"
    N_POSITIONAL: ClassVar[int] = 1


class Subsection(BaseMacro):
    """The \\subsection macro - second-level section heading.

    Example:
        Subsection(Raw("Background"))
    """

    MACRO_ID: ClassVar[str] = "subsection"
    N_POSITIONAL: ClassVar[int] = 1


class Subsubsection(BaseMacro):
    """The \\subsubsection macro - third-level section heading.

    Example:
        Subsubsection(Raw("Details"))
    """

    MACRO_ID: ClassVar[str] = "subsubsection"
    N_POSITIONAL: ClassVar[int] = 1


class Paragraph(BaseMacro):
    """The \\paragraph macro - fourth-level section heading.

    Example:
        Paragraph(Raw("Note"))
    """

    MACRO_ID: ClassVar[str] = "paragraph"
    N_POSITIONAL: ClassVar[int] = 1


class Subparagraph(BaseMacro):
    """The \\subparagraph macro - fifth-level section heading.

    Example:
        Subparagraph(Raw("Remark"))
    """

    MACRO_ID: ClassVar[str] = "subparagraph"
    N_POSITIONAL: ClassVar[int] = 1


# ============================================================================
# Font Size Macros  (declaration style: {\cmd content})
# ============================================================================


class _FontSize(BaseMacro, Protocol):
    """Base for font size declarations: {\\cmd content}."""

    N_POSITIONAL: ClassVar[int] = 1

    @override
    def serialize_indented(self, indent: int) -> str:
        from ...model.serialization import serialize_with_indent

        return f"{{\\{self.id} {serialize_with_indent(self.args[0], 0)}}}"


class Tiny(_FontSize):
    MACRO_ID: ClassVar[str] = "tiny"


class Small(_FontSize):
    MACRO_ID: ClassVar[str] = "small"


class Large(_FontSize):
    MACRO_ID: ClassVar[str] = "large"


class LargeLarge(_FontSize):
    MACRO_ID: ClassVar[str] = "Large"


class LargeLargeLarge(_FontSize):
    MACRO_ID: ClassVar[str] = "LARGE"


class Huge(_FontSize):
    MACRO_ID: ClassVar[str] = "huge"


class HugeHuge(_FontSize):
    MACRO_ID: ClassVar[str] = "Huge"


# ============================================================================
# Hyperlink Macro
# ============================================================================


class Href(BaseMacro):
    """The \\href macro - creates a hyperlink.

    Example:
        Href(Raw("https://example.com"), Raw("Example Site"))

    Note:
        Requires the hyperref package in your LaTeX document.
    """

    MACRO_ID: ClassVar[str] = "href"
    N_POSITIONAL: ClassVar[int] = 2
