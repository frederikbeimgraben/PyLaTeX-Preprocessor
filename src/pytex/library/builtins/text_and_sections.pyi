"""Type stubs for strongly-typed LaTeX builtin macros."""

from typing import Protocol, override

from pytex.model.base_macro import BaseMacro
from pytex.model.base_model import TeX

# ============================================================================
# Utility Macros
# ============================================================================

class _Relax(BaseMacro):
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
    """\\textbf — bold text. Example: Bold(Raw("important text"))"""
    def __init__(self, content: TeX | str) -> None: ...
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
    """\\textit — italic text. Example: Italic(Raw("emphasized text"))"""
    def __init__(self, content: TeX | str) -> None: ...
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
    """\\texttt — monospace text. Example: Texttt(Raw("code"))"""
    def __init__(self, content: TeX | str) -> None: ...
    @property
    @override
    def id(self) -> str: ...
    @property
    @override
    def n_positional(self) -> int: ...
    @property
    @override
    def keyword_args(self) -> dict[str, tuple[type[TeX], TeX]]: ...

class Underline(BaseMacro):
    """\\underline — underlined text."""
    def __init__(self, content: TeX | str) -> None: ...
    @property
    @override
    def id(self) -> str: ...
    @property
    @override
    def n_positional(self) -> int: ...
    @property
    @override
    def keyword_args(self) -> dict[str, tuple[type[TeX], TeX]]: ...

class Emph(BaseMacro):
    """\\emph — semantic emphasis."""
    def __init__(self, content: TeX | str) -> None: ...
    @property
    @override
    def id(self) -> str: ...
    @property
    @override
    def n_positional(self) -> int: ...
    @property
    @override
    def keyword_args(self) -> dict[str, tuple[type[TeX], TeX]]: ...

class SmallCaps(BaseMacro):
    """\\textsc — small capitals."""
    def __init__(self, content: TeX | str) -> None: ...
    @property
    @override
    def id(self) -> str: ...
    @property
    @override
    def n_positional(self) -> int: ...
    @property
    @override
    def keyword_args(self) -> dict[str, tuple[type[TeX], TeX]]: ...

class Superscript(BaseMacro):
    """\\textsuperscript — superscript text."""
    def __init__(self, content: TeX | str) -> None: ...
    @property
    @override
    def id(self) -> str: ...
    @property
    @override
    def n_positional(self) -> int: ...
    @property
    @override
    def keyword_args(self) -> dict[str, tuple[type[TeX], TeX]]: ...

class Subscript(BaseMacro):
    """\\textsubscript — subscript text."""
    def __init__(self, content: TeX | str) -> None: ...
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
    """\\section — top-level heading. Example: Section(Raw("Introduction"))"""
    def __init__(self, title: TeX | str) -> None: ...
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
    """\\subsection — second-level heading."""
    def __init__(self, title: TeX | str) -> None: ...
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
    """\\subsubsection — third-level heading."""
    def __init__(self, title: TeX | str) -> None: ...
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
    """\\paragraph — fourth-level heading."""
    def __init__(self, title: TeX | str) -> None: ...
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
    """\\subparagraph — fifth-level heading."""
    def __init__(self, title: TeX | str) -> None: ...
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
    """\\href — hyperlink. Requires hyperref. Example: Href(Raw("url"), Raw("text"))"""
    def __init__(self, url: TeX | str, text: TeX | str) -> None: ...
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
# Font Size Macros
# ============================================================================

class _FontSize(BaseMacro, Protocol):
    def __init__(self, content: TeX | str) -> None: ...
    @property
    @override
    def n_positional(self) -> int: ...
    @property
    @override
    def keyword_args(self) -> dict[str, tuple[type[TeX], TeX]]: ...
    @override
    def serialize_indented(self, indent: int) -> str: ...

class Tiny(_FontSize):
    """Font size: {\\tiny content}"""
    @property
    @override
    def id(self) -> str: ...

class Small(_FontSize):
    """Font size: {\\small content}"""
    @property
    @override
    def id(self) -> str: ...

class Large(_FontSize):
    """Font size: {\\large content}"""
    @property
    @override
    def id(self) -> str: ...

class LargeLarge(_FontSize):
    """Font size: {\\Large content}"""
    @property
    @override
    def id(self) -> str: ...

class LargeLargeLarge(_FontSize):
    """Font size: {\\LARGE content}"""
    @property
    @override
    def id(self) -> str: ...

class Huge(_FontSize):
    """Font size: {\\huge content}"""
    @property
    @override
    def id(self) -> str: ...

class HugeHuge(_FontSize):
    """Font size: {\\Huge content}"""
    @property
    @override
    def id(self) -> str: ...
