"""The optimize pass, which simplifies a `TeX` node tree.

The pass does two things. Both are render-equivalent.

1. It flattens nested `Concat` nodes and drops the child nodes that render
   to nothing. `Concat` itself does this when PyTeX rebuilds it.
2. It turns a `Raw` string that holds one whole LaTeX construct into the
   matching native node. Examples are `\\newpage`, `\\section{...}` and
   `\\begin{x}...\\end{x}`.

Each `Raw` conversion has a guard. PyTeX uses the new node only when the new
node renders to the same string as the original `Raw`. The whitespace just
inside `\\[..\\]` and `\\(..\\)` is the one exception. TeX ignores that
whitespace, so a candidate that differs only there still passes the guard.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, cast

from pytex.helpers.coerce import coerce_tex
from pytex.helpers.with_package import WithPackage
from pytex.interface.tex import TeX
from pytex.model.comment import Comment
from pytex.model.concat import Concat
from pytex.model.control_sequence import ControlSequence, Parameter
from pytex.model.environment import Environment
from pytex.model.math import DisplayMath, InlineMath, Math
from pytex.model.raw import PATTERN, Raw, pytex_namespace
from pytex.registry import Registry

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pytex.interface.control_sequence import Parameters, ParameterType

__all__ = ["Optimize"]

# Whole-string LaTeX shapes that a `Raw` can hold. The re-render guard makes a
# loose match safe, so these patterns stay simple on purpose.
_ENV = re.compile(r"\\begin\{([a-zA-Z@*]+)\}(.*)\\end\{\1\}", re.DOTALL)
_ONE_ARG = re.compile(r"\\([a-zA-Z@]+)\{([^{}]*)\}", re.DOTALL)
_BARE = re.compile(r"\\([a-zA-Z@]+)")

# Constructs that the pass finds inside a `Raw` and splits out into their own
# nodes. These are inline `pytex(...)` markers, line comments and math
# delimiters. `\\[` maps onto `DisplayMath`, `\\(` onto `Math`, and `$...$`
# onto `InlineMath`. The `$` body holds no `$` character, so `$$` cannot match
# across a display block.
_TOKEN = re.compile(
    rf"(?P<marker>{PATTERN.pattern})"
    # A comment owns the newline that ends it, so the `\n` is required. An
    # unterminated comment at the end of the file stays text, which keeps the
    # rendered string the same.
    + r"|(?<!\\)%(?P<comment>[^\n]*)\n"
    + r"|\\\[(?P<dmath>.*?)\\\]"
    + r"|\\\((?P<imath>.*?)\\\)"
    + r"|\$(?P<smath>[^$]*)\$",
    re.DOTALL,
)


@Registry.add
def Optimize(body: TeX | str) -> TeX:
    """Return a simpler, render-equivalent version of `body`."""
    return _optimize(coerce_tex(body))


def _optimize(node: TeX) -> TeX:
    if isinstance(node, Concat):
        return _optimize_concat(node)
    if isinstance(node, WithPackage):
        return WithPackage(_optimize(cast("TeX", node.child)), node.package)
    if isinstance(node, ControlSequence):
        cs = cast("ControlSequence[Parameters]", node)
        params = cast("Parameters", tuple(_optimize(p) for p in (cs.params or ())))
        return ControlSequence(cs.name, params, cs.required_packages)
    if isinstance(node, Parameter):
        value = cast("Parameter[ParameterType]", node).value
        return Parameter(
            _optimize(value) if isinstance(value, TeX) else value,
            optional=node.optional,
        )
    if isinstance(node, Raw):
        return _native(node)
    return node


def _optimize_concat(node: Concat) -> TeX:
    parts: list[TeX] = []
    for element in node.elements:
        optimized = _optimize(element)
        # Concatenation is associative, so flattening a nested `Concat` does
        # not change the rendered string. Keep a `\begin{}...\end{}` group
        # together, because the pass must still recognize it as an
        # environment.
        if isinstance(optimized, Concat) and not _is_environment(optimized):
            parts.extend(optimized.elements)
        else:
            parts.append(optimized)
    # `Concat` drops the empty parts and unwraps a single child when PyTeX
    # constructs it.
    return Concat(*parts)


def _is_environment(concat: Concat) -> bool:
    kids = concat.elements
    return (
        len(kids) >= 2
        and isinstance(kids[0], ControlSequence)
        and kids[0].name == "begin"
        and isinstance(kids[-1], ControlSequence)
        and kids[-1].name == "end"
    )


def _native(raw: Raw) -> TeX:
    """Turn a `Raw` into native nodes when this is safe.

    The function tries two steps. First it splits out the constructs that
    `_TOKEN` matches. These are inline `pytex(...)` markers, comments, and
    `\\[...\\]` and `\\(...\\)` math. Then it tries to turn a `Raw` that holds
    one whole LaTeX construct into the matching node. Re-render equality
    guards both steps, so the meaning stays the same.

    Returns:
        The native nodes, or the original `Raw` when neither step matches.
    """
    tokenized = _tokenize(raw)
    if tokenized is not None:
        return tokenized
    if "\\" not in raw.content:
        return raw
    target = raw.rendered
    for candidate in _candidates(raw.content):
        if candidate.rendered == target:
            return candidate
    return raw


_MATH_OPEN = re.compile(r"(\\[\[(])\s+")
_MATH_CLOSE = re.compile(r"\s+(\\[\])])")


def _strip_math_ws(text: str) -> str:
    r"""Drop the whitespace just inside `\[..\]` and `\(..\)`.

    TeX math mode ignores that whitespace. Two strings that differ only there
    give the same printed result. A `DisplayMath` node and a `Math` node trim
    that whitespace. The tokenizer uses this function so that it still accepts
    such a candidate as equal to the original string.
    """
    return _MATH_CLOSE.sub(r"\1", _MATH_OPEN.sub(r"\1", text))


def _tokenize(raw: Raw) -> TeX | None:
    """Split a `Raw` into literal text and the native nodes that `_TOKEN` finds.

    Returns:
        The split nodes. The result is `None` when `_TOKEN` matches nothing,
        or when the split would change the rendered string. Whitespace inside
        the math delimiters is the one exception, because TeX ignores it.
    """
    content = raw.content
    namespace = pytex_namespace(raw.namespace or {})
    parts: list[TeX] = []
    cursor = 0
    for match in _TOKEN.finditer(content):
        if match.start() > cursor:
            parts.append(
                _optimize(
                    Raw(content[cursor : match.start()], allow_replacements=False)
                )
            )
        # `_token_node` already applies `_optimize` where that is needed, for
        # example inside the `dmath`, `imath` and `smath` branches. Running
        # `_optimize` on its result again would re-scan an inert marker Raw
        # for the same `pytex(...)` marker forever, so this loop must not do
        # that a second time.
        parts.append(_token_node(match, raw.allow_replacements, namespace))
        cursor = match.end()
    if not parts:
        return None
    if cursor < len(content):
        parts.append(_optimize(Raw(content[cursor:], allow_replacements=False)))
    candidate = Concat(*parts)
    rendered = candidate.rendered
    target = raw.rendered
    if rendered == target or _strip_math_ws(rendered) == _strip_math_ws(target):
        return candidate
    return None


def _token_node(
    match: re.Match[str], allow_replacements: bool, namespace: dict[str, object]
) -> TeX:
    if match.group("marker") is not None:
        if not allow_replacements:
            return Raw(match.group(0), allow_replacements=False)
        result = cast("object", eval(match.group("expr"), namespace))
        if isinstance(result, TeX):
            return result
        return Raw(str(result), allow_replacements=False)
    if (comment := match.group("comment")) is not None:
        return Comment(comment)
    if (dmath := match.group("dmath")) is not None:
        return DisplayMath(
            _optimize(
                Raw(dmath, namespace=namespace, allow_replacements=allow_replacements)
            )
        )
    if (imath := match.group("imath")) is not None:
        return Math(
            _optimize(
                Raw(imath, namespace=namespace, allow_replacements=allow_replacements)
            )
        )
    return InlineMath(
        _optimize(
            Raw(
                match.group("smath"),
                namespace=namespace,
                allow_replacements=allow_replacements,
            )
        )
    )


def _candidates(content: str) -> Iterator[TeX]:
    if (match := _ENV.fullmatch(content)) is not None:
        yield Environment(match.group(1), _optimize(Raw(match.group(2))))
    if (match := _ONE_ARG.fullmatch(content)) is not None:
        yield ControlSequence(
            match.group(1), (Parameter(_optimize(Raw(match.group(2)))),)
        )
    if (match := _BARE.fullmatch(content)) is not None:
        yield ControlSequence(match.group(1), ())
