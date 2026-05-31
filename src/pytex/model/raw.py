# pyright: reportAny=false
import re
from dataclasses import dataclass, field
from typing import override

from ..interface.tex import TeX
from ..registry import Registry


def _nested_inner(depth: int) -> str:
    inner = r"[^()]*"
    for _ in range(depth):
        inner = rf"(?:[^()]|\({inner}\))*"
    return inner


_PATTERN = re.compile(
    rf"\\iffalse\s*\{{\s*pytex\s*\((?P<expr>{_nested_inner(8)})\)\s*\}}\s*\\fi",
    re.DOTALL,
)


def _evaluate(content: str, extra: dict[str, object]) -> str:
    namespace: dict[str, object] = {
        "__builtins__": __builtins__,
        **Registry.namespace(),
        **extra,
    }

    def _sub(match: re.Match[str]) -> str:
        return str(eval(match.group("expr"), namespace))  # noqa: S307

    return _PATTERN.sub(_sub, content)


@Registry.add
@dataclass
class Raw(TeX):
    content: str
    namespace: dict[str, object] | None = field(default=None)
    allow_replacements: bool = True

    @property
    @override
    def rendered(self) -> str:
        if not self.allow_replacements or "\\iffalse" not in self.content:
            return self.content
        return _evaluate(self.content, self.namespace or {})
