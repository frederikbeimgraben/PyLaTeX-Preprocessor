"""Factories for the LaTeX `picture` environment."""

from ..interface.tex import TeX
from ..model.concat import Concat
from ..model.raw import Raw
from ..registry import Registry

__all__ = ["Picture", "Put"]


@Registry.add
def Picture(
    width: str,
    height: str,
    body: TeX | str,
    x_offset: str = "0",
    y_offset: str = "0",
) -> TeX:
    """Render a `picture` environment with a size and an origin offset.

    The `picture` environment takes its arguments in parentheses, not in
    braces. The factory writes the LaTeX text directly, because `Parameter`
    renders braces or square brackets only.

    Args:
        width: The width in units of `\\unitlength`.
        height: The height in units of `\\unitlength`.
        x_offset: The x coordinate of the lower left corner.
        y_offset: The y coordinate of the lower left corner.
    """
    return Concat(
        Raw(f"\\begin{{picture}}({width},{height})({x_offset},{y_offset})"),
        body,
        Raw("\\end{picture}"),
    )


@Registry.add
def Put(x: str, y: str, body: TeX | str) -> TeX:
    """Render `\\put`, which places the body at a point inside a picture.

    Args:
        x: The x coordinate in units of `\\unitlength`.
        y: The y coordinate in units of `\\unitlength`.
    """
    return Concat(
        Raw(f"\\put({x},{y}){{"),
        body,
        Raw("}"),
    )
