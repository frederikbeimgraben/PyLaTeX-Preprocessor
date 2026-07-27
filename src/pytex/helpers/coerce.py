"""Coerce a plain value into a TeX node."""

from ..interface.tex import TeX
from ..model.raw import Raw
from ..registry import Registry

__all__ = ["coerce_tex"]


@Registry.add
def coerce_tex(value: TeX | str) -> TeX:
    """Return a TeX node for `value`. A string becomes a `Raw` node.

    Note:
        `Raw` escapes nothing and it evaluates an inline `pytex(...)` marker.
        If the string comes from a source you do not trust, call `Sanitize`
        instead.
    """
    if isinstance(value, TeX):
        return value

    return Raw(value)
