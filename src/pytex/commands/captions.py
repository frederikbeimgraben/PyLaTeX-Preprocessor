"""Caption factories for the LaTeX kernel and for `caption` and `subcaption`."""

from ..helpers.with_package import with_package
from ..interface.tex import TeX
from ..model.control_sequence import ControlSequence, Parameter
from ..packages import CAPTION, SUBCAPTION
from ..registry import Registry

__all__ = [
    "Caption",
    "Captionof",
    "Captionsetup",
    "Subcaption",
    "Subcaptionbox",
    "Subref",
]


@Registry.add
def Caption(text: TeX | str, short: TeX | str | None = None) -> TeX:
    """Render `\\caption` for a figure or a table.

    Args:
        short: The short caption for the list of figures or the list of
            tables. If `short` is None, LaTeX uses the full text there.
    """
    if short is None:
        return ControlSequence("caption", (Parameter(text),))
    return ControlSequence(
        "caption",
        (Parameter(short, optional=True), Parameter(text)),
    )


@Registry.add
@with_package(CAPTION)
def Captionof(typ: str, text: TeX | str) -> TeX:
    """Render `\\captionof`, a caption outside a float environment.

    Args:
        typ: The float type the caption counts against, for example `figure`.
    """
    return ControlSequence("captionof", (Parameter(typ), Parameter(text)))


@Registry.add
@with_package(CAPTION)
def Captionsetup(options: dict[str, str]) -> TeX:
    """Render `\\captionsetup`, which sets the caption format.

    Args:
        options: Caption options. The factory renders them as `key=value`
            pairs and joins the pairs with commas.
    """
    return ControlSequence("captionsetup", (Parameter(options),))


@Registry.add
@with_package(SUBCAPTION)
def Subcaption(text: TeX | str) -> TeX:
    """Render `\\subcaption`, the caption of a subfigure or a subtable."""
    return ControlSequence("subcaption", (Parameter(text),))


@Registry.add
@with_package(SUBCAPTION)
def Subcaptionbox(caption: TeX | str, body: TeX | str) -> TeX:
    """Render `\\subcaptionbox`, a sub-float box with its own caption."""
    return ControlSequence(
        "subcaptionbox",
        (Parameter(caption), Parameter(body)),
    )


@Registry.add
@with_package(SUBCAPTION)
def Subref(label: str) -> TeX:
    """Render `\\subref`, which prints the sub-float number without the parent."""
    return ControlSequence("subref", (Parameter(label),))
