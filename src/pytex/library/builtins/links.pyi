"""Type stubs for the hyperlink builtin macro."""

from pytex.model.base_macro import BaseMacro
from pytex.model.base_model import TeX

class Href(BaseMacro):
    """\\href — hyperlink. Requires hyperref. Example: Href(Raw("url"), Raw("text"))"""
    def __init__(self, url: TeX | str, text: TeX | str) -> None: ...
