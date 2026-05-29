from dataclasses import dataclass
from typing import override

from model.base_macro import SimpleMacro
from model.base_model import TeX
from model.helpers import CLOSING_BRACE, OPENING_BRACE


@dataclass
class DeclareRobustCommand(SimpleMacro("DeclareRobustCommand", 3)):
    cmd_key: str
    content: TeX

    n_args: int = 0
    default: TeX | None = None

    @override
    def serialize(self) -> str:
        return (
            f"\\{self.id}{OPENING_BRACE}\\{self.cmd_key}{CLOSING_BRACE}[{self.n_args}]"
            + f"[{self.default.serialize()}]"
            if self.default is not None
            else "" + f"{OPENING_BRACE}\\{self.content.serialize()}{CLOSING_BRACE}"
        )


@dataclass
class RedeclareRobustCommand(SimpleMacro("RedeclareRobustCommand", 3)):
    cmd_key: str
    content: TeX

    n_args: int = 0
    default: TeX | None = None

    @override
    def serialize(self) -> str:
        return (
            f"\\{self.id}{OPENING_BRACE}\\{self.cmd_key}{CLOSING_BRACE}[{self.n_args}]"
            + f"[{self.default.serialize()}]"
            if self.default is not None
            else "" + f"{OPENING_BRACE}\\{self.content.serialize()}{CLOSING_BRACE}"
        )
