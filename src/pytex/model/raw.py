# pyright: reportAny=false
import re
from dataclasses import dataclass, field
from typing import override

from ..interface.tex import TeX
from ..registry import Registry

_START = re.compile(r"\\iffalse\s*\{\s*pytex\s*\(", re.DOTALL)
_END = re.compile(r"\)\s*\}\s*\\fi", re.DOTALL)


def _evaluate(content: str, extra: dict[str, object]) -> str:
    namespace: dict[str, object] = {
        "__builtins__": __builtins__,
        **Registry.namespace(),
        **extra,
    }
    out: list[str] = []
    i = 0
    while True:
        m = _START.search(content, i)
        if m is None:
            out.append(content[i:])
            break
        out.append(content[i : m.start()])
        depth = 1
        j = m.end()
        while j < len(content) and depth > 0:
            ch = content[j]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        if depth != 0:
            raise ValueError(f"unbalanced parens in pytex eval at offset {m.start()}")
        expr = content[m.end() : j]
        end_m = _END.match(content, j)
        if end_m is None:
            raise ValueError(f"missing `)}}\\fi` terminator at offset {j}")
        result = eval(expr, namespace)  # noqa: S307
        out.append(str(result))
        i = end_m.end()
    return "".join(out)


@Registry.add
@dataclass
class Raw(TeX):
    content: str
    namespace: dict[str, object] | None = field(default=None)

    @property
    @override
    def rendered(self) -> str:
        if "\\iffalse" not in self.content:
            return self.content
        return _evaluate(self.content, self.namespace or {})
