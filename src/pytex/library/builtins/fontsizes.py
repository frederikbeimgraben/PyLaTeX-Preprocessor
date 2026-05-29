"""Font size builtin macros (declaration style: {\\cmd content})."""

from typing import ClassVar, Protocol, override

from ...model.base_macro import BaseMacro


class _FontSize(BaseMacro, Protocol):
    """Base for font size declarations: {\\cmd content}."""

    N_POSITIONAL: ClassVar[int] = 1

    @override
    def serialize_indented(self, indent: int) -> str:
        from ...model.serialization import serialize_with_indent

        return f"{{\\{self.id} {serialize_with_indent(self.args[0], 0)}}}"


class Tiny(_FontSize):
    MACRO_ID: ClassVar[str] = "tiny"


class Small(_FontSize):
    MACRO_ID: ClassVar[str] = "small"


class Large(_FontSize):
    MACRO_ID: ClassVar[str] = "large"


class LargeLarge(_FontSize):
    MACRO_ID: ClassVar[str] = "Large"


class LargeLargeLarge(_FontSize):
    MACRO_ID: ClassVar[str] = "LARGE"


class Huge(_FontSize):
    MACRO_ID: ClassVar[str] = "huge"


class HugeHuge(_FontSize):
    MACRO_ID: ClassVar[str] = "Huge"
