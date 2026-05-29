"""Section heading builtin macros (\\section, \\subsection, ...)."""

from typing import ClassVar

from ...model.base_macro import BaseMacro


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
