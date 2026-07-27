# pyright: reportAny=false
import re
from dataclasses import dataclass, field
from typing import override

from ..interface.tex import TeX
from ..registry import Registry

__all__ = ["Raw", "pytex_namespace"]


def _nested_inner(depth: int) -> str:
    """Build a regex fragment that matches balanced parentheses to `depth`.

    A regular expression cannot match parentheses that nest without a limit, so
    `PATTERN` supports a fixed depth only. An expression that nests deeper does
    not match, and the marker stays in the rendered `.tex` file.
    """
    inner = r"[^()]*"
    for _ in range(depth):
        inner = rf"(?:[^()]|\({inner}\))*"
    return inner


PATTERN = re.compile(
    rf"\\iffalse\s*\{{\s*pytex\s*\((?P<expr>{_nested_inner(8)})\)\s*\}}\s*\\fi",
    re.DOTALL,
)


def pytex_namespace(extra: dict[str, object] | None = None) -> dict[str, object]:
    """Build the namespace that `eval` uses for a `pytex(...)` expression.

    The namespace holds the Python builtins and every factory in the
    `Registry`. The same names therefore work in both code-execution surfaces:
    the inline `pytex(...)` marker `\\iffalse{pytex(...)}\\fi` in a `.tex` file,
    and `[//]: # "..."` in Markdown.

    Args:
        extra: More names to add. A name in `extra` replaces a registry name.
            None adds no name.
    """
    return {
        "__builtins__": __builtins__,
        **Registry.namespace(),
        **(extra or {}),
    }


def _evaluate(content: str, extra: dict[str, object]) -> str:
    namespace = pytex_namespace(extra)

    def _sub(match: re.Match[str]) -> str:
        return str(eval(match.group("expr"), namespace))

    return PATTERN.sub(_sub, content)


@Registry.add
@dataclass
class Raw(TeX):
    """Literal LaTeX source that PyTeX does not escape.

    `rendered` returns `content` as written, except for the inline
    `pytex(...)` markers that `allow_replacements` enables.

    Attributes:
        namespace: Extra names for the inline `pytex(...)` markers. None means
            no extra names.
        allow_replacements: True makes `rendered` run each inline `pytex(...)`
            marker in `content` as Python code. This is code execution by
            design. Pass False for content from a source you do not trust.
    """

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
