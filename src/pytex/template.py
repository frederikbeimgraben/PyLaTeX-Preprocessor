r"""`tex(t"...")` — build a `TeX` tree from a template string (PEP 750).

Requires Python 3.14 (the ``t"..."`` syntax and :mod:`string.templatelib`).
This module is import-safe on older versions — it contains no t-string literals
and guards the runtime import — but :func:`tex` can only be called with a real
``Template``, which cannot exist before 3.14. ``pytex`` only re-exports it on
3.14+.

The rendering model mirrors the escape boundary a LaTeX document needs:

* static template parts are literal LaTeX (author-written, trusted);
* interpolations are escaped when they are plain values, spliced as-is when
  they are `TeX` nodes, and recursed when they are nested template strings or
  iterables of the above.

    name = "Q&A: 50%"
    tex(t"{Bold('Heading')} - {name}")   # node spliced; name -> "Q\&A: 50\%"
"""

# `string.templatelib` has no type stub before 3.14, so a type-checker running
# on an older Python cannot type the `Template` import; silence that noise for
# this module only (its logic is exercised on 3.14 in CI / the docker test).
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


# Real `Template` class at runtime (3.14+) for the nested-template check; an
# empty tuple on older versions makes the isinstance test always False.
try:
    from string.templatelib import Template

    _template_classes = (Template,)
except ImportError:  # Python < 3.14
    _template_classes = ()

_TEMPLATE_TYPES: tuple[type, ...] = _template_classes

__all__ = ["tex"]

_CONVERSIONS = {"r": repr, "s": str, "a": ascii}


def tex(template: _Template) -> TeX:
    """Render a t-string into a `TeX` tree (see the module docstring)."""
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
