"""Type stubs for strongly-typed LaTeX builtin macros.

Only the public constructor signatures are declared here; ``id``,
``n_positional`` and ``keyword_args`` are inherited from ``BaseMacro``.
"""

from typing import Protocol, override

from pytex.model.base_macro import BaseMacro
from pytex.model.base_model import TeX

# ============================================================================
# Utility Macros
# ============================================================================

class _Relax(BaseMacro):
    def __init__(self) -> None: ...

Relax: _Relax

class _Newline(BaseMacro):
    def __init__(self) -> None: ...

Newline: _Newline

# ============================================================================
# Text Formatting Macros
# ============================================================================

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

# ============================================================================
# Section Heading Macros
# ============================================================================

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

# ============================================================================
# Hyperlink Macro
# ============================================================================

class Href(BaseMacro):
    """\\href — hyperlink. Requires hyperref. Example: Href(Raw("url"), Raw("text"))"""
    def __init__(self, url: TeX | str, text: TeX | str) -> None: ...

# ============================================================================
# Font Size Macros
# ============================================================================

class _FontSize(BaseMacro, Protocol):
    def __init__(self, content: TeX | str) -> None: ...
    @override
    def serialize_indented(self, indent: int) -> str: ...

class Tiny(_FontSize):
    """Font size: {\\tiny content}"""

class Small(_FontSize):
    """Font size: {\\small content}"""

class Large(_FontSize):
    """Font size: {\\large content}"""

class LargeLarge(_FontSize):
    """Font size: {\\Large content}"""

class LargeLargeLarge(_FontSize):
    """Font size: {\\LARGE content}"""

class Huge(_FontSize):
    """Font size: {\\huge content}"""

class HugeHuge(_FontSize):
    """Font size: {\\Huge content}"""
