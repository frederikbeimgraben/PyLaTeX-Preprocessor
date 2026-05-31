from typing import Final

from pytex.interface.tex import TeX
from pytex.model.color import Color
from pytex.model.control_sequence import ControlSequence, Parameter
from pytex.model.raw import Raw
from pytex.registry import Registry

type HyperOption = bool | int | str | TeX

HSRT_CITE_COLOR: Final[Color] = Color.rgb(0.286, 0.427, 0.537, name="hsrtcite")
HSRT_LINK_COLOR: Final[Color] = Color.rgb(0.161, 0.310, 0.427, name="hsrtlink")
HSRT_URL_COLOR: Final[Color] = Color.rgb(0.071, 0.212, 0.322, name="hsrturl")


HSRT_HYPER_OPTIONS: Final[dict[str, HyperOption]] = {
    "pdfpagemode": "UseOutlines",
    "bookmarksopen": True,
    "bookmarksopenlevel": 0,
    "hypertexnames": False,
    "colorlinks": True,
    "citecolor": HSRT_CITE_COLOR,
    "linkcolor": HSRT_LINK_COLOR,
    "urlcolor": HSRT_URL_COLOR,
    "pdfstartview": "FitV",
    "unicode": True,
    "breaklinks": True,
}


def _format(value: HyperOption) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, TeX):
        return value.rendered
    return str(value)


@Registry.add
def HSRTHyperref() -> TeX:
    """Hypersetup using `HSRT_HYPER_OPTIONS` (structured Python, not a TeX blob)."""
    body = ",".join(f"{k}={_format(v)}" for k, v in HSRT_HYPER_OPTIONS.items())
    return ControlSequence("hypersetup", (Parameter(Raw(body)),))
