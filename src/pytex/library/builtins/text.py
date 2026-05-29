"""Text formatting builtin macros (\\textbf, \\textit, ...)."""

from typing import ClassVar

from ...model.base_macro import BaseMacro


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
