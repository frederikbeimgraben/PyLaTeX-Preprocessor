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
    """`\\begin{picture}(W,H)(x,y) ... \\end{picture}` — non-standard arg syntax."""
    return Concat(
        Raw(f"\\begin{{picture}}({width},{height})({x_offset},{y_offset})"),
        body,
        Raw("\\end{picture}"),
    )


@Registry.add
def Put(x: str, y: str, body: TeX | str) -> TeX:
    """`\\put(x,y){body}` — picture-mode placement."""
    return Concat(
        Raw(f"\\put({x},{y}){{"),
        body,
        Raw("}"),
    )
