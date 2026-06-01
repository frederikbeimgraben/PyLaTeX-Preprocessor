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


def pytex_namespace(extra: dict[str, object] | None = None) -> dict[str, object]:
    """Namespace used to ``eval`` ``pytex(...)`` expressions.

    Exposes Python builtins plus every Registry-registered factory, so the same
    names work in both escape hatches: ``\\iffalse{pytex(...)}\\fi`` (TeX) and
    ``[//]: # "..."`` (Markdown).
    """
    return {
        "__builtins__": __builtins__,
        **Registry.namespace(),
        **(extra or {}),
    }


def _evaluate(content: str, extra: dict[str, object]) -> str:
    namespace = pytex_namespace(extra)

    def _sub(match: re.Match[str]) -> str:
        return str(eval(match.group("expr"), namespace))  # noqa: S307

    return _PATTERN.sub(_sub, content)


@Registry.add
@dataclass
class Raw(TeX):
    content: str
    namespace: dict[str, object] | None = field(default=None)
    allow_replacements: bool = True
    _parent: "TeX | None" = field(default=None, init=False, compare=False, repr=False)

    @property
    @override
    def rendered(self) -> str:
        if not self.allow_replacements or "\\iffalse" not in self.content:
            return self.content
        return _evaluate(self.content, self.namespace or {})
