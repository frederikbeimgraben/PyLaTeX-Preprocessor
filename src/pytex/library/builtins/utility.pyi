"""Type stubs for utility builtin macros."""

from pytex.model.base_macro import BaseMacro

class _Relax(BaseMacro):
    def __init__(self) -> None: ...

Relax: _Relax

class _Newline(BaseMacro):
    def __init__(self) -> None: ...

Newline: _Newline
