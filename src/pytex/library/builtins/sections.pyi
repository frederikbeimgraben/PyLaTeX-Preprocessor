"""Type stubs for section heading builtin macros."""

from pytex.model.base_macro import BaseMacro
from pytex.model.base_model import TeX

class Section(BaseMacro):
    """\\section — top-level heading. Example: Section(Raw("Introduction"))"""
    def __init__(self, title: TeX | str) -> None: ...

class Subsection(BaseMacro):
    """\\subsection — second-level heading."""
    def __init__(self, title: TeX | str) -> None: ...

class Subsubsection(BaseMacro):
    """\\subsubsection — third-level heading."""
    def __init__(self, title: TeX | str) -> None: ...

class Paragraph(BaseMacro):
    """\\paragraph — fourth-level heading."""
    def __init__(self, title: TeX | str) -> None: ...

class Subparagraph(BaseMacro):
    """\\subparagraph — fifth-level heading."""
    def __init__(self, title: TeX | str) -> None: ...
