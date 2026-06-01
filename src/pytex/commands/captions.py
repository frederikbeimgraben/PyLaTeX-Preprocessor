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
    if short is None:
        return ControlSequence("caption", (Parameter(text),))
    return ControlSequence(
        "caption",
        (Parameter(short, optional=True), Parameter(text)),
    )


@Registry.add
def Captionof(typ: str, text: TeX | str) -> TeX:
    return ControlSequence("captionof", (Parameter(typ), Parameter(text)))


@Registry.add
@with_package(CAPTION)
def Captionsetup(options: dict[str, str]) -> TeX:
    return ControlSequence("captionsetup", (Parameter(options),))


@Registry.add
@with_package(SUBCAPTION)
def Subcaption(text: TeX | str) -> TeX:
    return ControlSequence("subcaption", (Parameter(text),))


@Registry.add
@with_package(SUBCAPTION)
def Subcaptionbox(caption: TeX | str, body: TeX | str) -> TeX:
    return ControlSequence(
        "subcaptionbox",
        (Parameter(caption), Parameter(body)),
    )


@Registry.add
@with_package(SUBCAPTION)
def Subref(label: str) -> TeX:
    return ControlSequence("subref", (Parameter(label),))
