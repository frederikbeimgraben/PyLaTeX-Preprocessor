"""Type stubs for font size builtin macros."""

from typing import Protocol, override

from pytex.model.base_macro import BaseMacro
from pytex.model.base_model import TeX

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
