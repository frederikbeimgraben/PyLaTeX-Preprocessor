"""Utility builtin macros: \\relax and \\\\ (line break)."""

from typing import ClassVar

from ...model.base_macro import BaseMacro


class _Relax(BaseMacro):
    """The \\relax macro - does nothing, used as a no-op or separator."""

    MACRO_ID: ClassVar[str] = "relax"


Relax = _Relax()


class _Newline(BaseMacro):
    """The \\\\ (newline/line break) macro."""

    MACRO_ID: ClassVar[str] = "\\"


Newline = _Newline()
