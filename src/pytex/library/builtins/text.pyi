"""Type stubs for text formatting builtin macros."""

from pytex.model.base_macro import BaseMacro
from pytex.model.base_model import TeX

class Bold(BaseMacro):
    """\\textbf — bold text. Example: Bold(Raw("important text"))"""
    def __init__(self, content: TeX | str) -> None: ...

class Italic(BaseMacro):
    """\\textit — italic text. Example: Italic(Raw("emphasized text"))"""
    def __init__(self, content: TeX | str) -> None: ...

class Texttt(BaseMacro):
    """\\texttt — monospace text. Example: Texttt(Raw("code"))"""
    def __init__(self, content: TeX | str) -> None: ...

class Underline(BaseMacro):
    """\\underline — underlined text."""
    def __init__(self, content: TeX | str) -> None: ...

class Emph(BaseMacro):
    """\\emph — semantic emphasis."""
    def __init__(self, content: TeX | str) -> None: ...

class SmallCaps(BaseMacro):
    """\\textsc — small capitals."""
    def __init__(self, content: TeX | str) -> None: ...

class Superscript(BaseMacro):
    """\\textsuperscript — superscript text."""
    def __init__(self, content: TeX | str) -> None: ...

class Subscript(BaseMacro):
    """\\textsubscript — subscript text."""
    def __init__(self, content: TeX | str) -> None: ...
