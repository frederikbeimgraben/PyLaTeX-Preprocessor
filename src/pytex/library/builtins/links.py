"""Hyperlink builtin macro (\\href)."""

from typing import ClassVar

from ...model.base_macro import BaseMacro


class Href(BaseMacro):
    """The \\href macro - creates a hyperlink.

    Example:
        Href(Raw("https://example.com"), Raw("Example Site"))

    Note:
        Requires the hyperref package in your LaTeX document.
    """

    MACRO_ID: ClassVar[str] = "href"
    N_POSITIONAL: ClassVar[int] = 2
