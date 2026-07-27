r"""Build a node tree from a template string with `tex(t"...")` (PEP 750).

`tex` needs Python 3.14 or later for the `t"..."` syntax and for
`string.templatelib`. This module stays import-safe on an older Python. It
holds no t-string literal and it guards the runtime import. You can call `tex`
only with a real `Template`, and a `Template` cannot exist before Python 3.14.
`pytex` re-exports `tex` only on Python 3.14 and later.

The conversion follows the escape boundary that a LaTeX document needs. PyTeX
trusts the static parts of the template, because the author wrote them, and
keeps them as literal LaTeX. For each interpolation, `tex` uses one of these
rules:

1. `tex` puts a TeX node into the node tree without a change.
2. `tex` converts a nested template string, a list, or a tuple one item at a
   time.
3. `tex` formats any other value, then escapes it.

Example:
    name = "Q&A: 50%"
    tex(t"{Bold('Heading')} - {name}")

    The `Bold` node goes into the node tree without a change. PyTeX escapes
    `name` to "Q\&A: 50\%".
"""

# `string.templatelib` has no type stub before Python 3.14. A type-checker on
# an older Python cannot type the `Template` import, so silence that noise for
# this module only. CI and the docker test exercise the logic on Python 3.14.
# pyright: reportMissingImports=false, reportUnknownVariableType=false
from __future__ import annotations

from typing import TYPE_CHECKING, cast

from .helpers.sanitize import escape_latex
from .interface.tex import TeX
from .model.concat import Concat
from .model.empty import Empty
from .model.raw import Raw

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Protocol

    class _Interpolation(Protocol):
        @property
        def value(self) -> object: ...
        @property
        def conversion(self) -> str | None: ...
        @property
        def format_spec(self) -> str: ...

    class _Template(Protocol):
        def __iter__(self) -> Iterator[str | _Interpolation]: ...


# On Python 3.14 and later this holds the real `Template` class for the
# nested-template check. On an older Python it is an empty tuple, which makes
# the isinstance test always False.
try:
    from string.templatelib import Template

    _template_classes = (Template,)
except ImportError:  # Python < 3.14
    _template_classes = ()

_TEMPLATE_TYPES: tuple[type, ...] = _template_classes

__all__ = ["tex"]

_CONVERSIONS = {"r": repr, "s": str, "a": ascii}


def tex(template: _Template) -> TeX:
    """Convert a template string into a node tree.

    See the module docstring for the escape rules.
    """
    return Concat(
        *(
            Raw(item)  # literal LaTeX
            if isinstance(item, str)
            else _coerce(item.value, item.conversion, item.format_spec)
            for item in template
        )
    )


def _coerce(value: object, conversion: str | None = None, spec: object = "") -> TeX:
    if value is None:
        return Empty
    if isinstance(value, TeX):
        return value
    if isinstance(value, _TEMPLATE_TYPES):
        return tex(cast("_Template", value))
    if isinstance(value, (list, tuple)):
        items = cast("tuple[object, ...] | list[object]", value)
        return Concat(*(_coerce(item) for item in items))
    if conversion in _CONVERSIONS:
        value = _CONVERSIONS[conversion](value)
    text = format(value, spec if isinstance(spec, str) else "")
    return Raw(escape_latex(text))
