"""`Optimize` - simplify a `TeX` tree without changing what it renders.

Two passes, both render-preserving:

* structural - flatten nested `Concat`s and drop nodes that render to nothing
  (handled by `Concat` itself on reconstruction);
* recognition - turn `Raw` strings that are really a single LaTeX construct
  (``\\newpage``, ``\\section{...}``, ``\\begin{x}...\\end{x}``) into the
  matching native nodes.

Every `Raw` conversion is guarded: the candidate node is only used when it
renders to exactly the same string as the original, so `Optimize(x).rendered
== x.rendered` always holds.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, cast

from pytex.helpers.coerce import coerce_tex
from pytex.helpers.with_package import WithPackage
from pytex.interface.tex import TeX
from pytex.model.concat import Concat
from pytex.model.control_sequence import ControlSequence, Parameter
from pytex.model.environment import Environment
from pytex.model.raw import Raw
from pytex.registry import Registry

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pytex.interface.control_sequence import Parameters, ParameterType

__all__ = ["Optimize"]

# Whole-string LaTeX shapes a Raw might carry. The guard (re-render equality)
# makes loose matches safe, so these stay deliberately simple.
_ENV = re.compile(r"\\begin\{([a-zA-Z@*]+)\}(.*)\\end\{\1\}", re.DOTALL)
_ONE_ARG = re.compile(r"\\([a-zA-Z@]+)\{([^{}]*)\}", re.DOTALL)
_BARE = re.compile(r"\\([a-zA-Z@]+)")


@Registry.add
def Optimize(body: TeX | str) -> TeX:
    """Return a render-equivalent but simpler version of `body`."""
    return _optimize(coerce_tex(body))


def _optimize(node: TeX) -> TeX:
    if isinstance(node, Concat):
        return _optimize_concat(node)
    if isinstance(node, WithPackage):
        return WithPackage(_optimize(cast("TeX", node.child)), node.package)
    if isinstance(node, ControlSequence):
        cs = cast("ControlSequence[Parameters]", node)
        params = cast(
            "Parameters", tuple(_optimize(p) for p in (cs.params or ()))
        )
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
        # Flatten nested Concats (concatenation is associative, so the rendered
        # string is unchanged) - but keep a `\begin{}...\end{}` group together so
        # it stays recognisable as an environment.
        if isinstance(optimized, Concat) and not _is_environment(optimized):
            parts.extend(optimized.elements)
        else:
            parts.append(optimized)
    # `Concat` drops empties and unwraps a single child on construction.
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
    """Convert a `Raw` that is one whole LaTeX construct to a native node.

    Falls back to the original `Raw` unless a candidate renders identically.
    """
    if "\\" not in raw.content:
        return raw
    target = raw.rendered
    for candidate in _candidates(raw.content):
        if candidate.rendered == target:
            return candidate
    return raw


def _candidates(content: str) -> Iterator[TeX]:
    if (match := _ENV.fullmatch(content)) is not None:
        yield Environment(match.group(1), _optimize(Raw(match.group(2))))
    if (match := _ONE_ARG.fullmatch(content)) is not None:
        yield ControlSequence(
            match.group(1), (Parameter(_optimize(Raw(match.group(2)))),)
        )
    if (match := _BARE.fullmatch(content)) is not None:
        yield ControlSequence(match.group(1), ())
