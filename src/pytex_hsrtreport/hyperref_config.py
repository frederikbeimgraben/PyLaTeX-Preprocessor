from typing import Final

from pytex.commands.hyperref import Hypersetup
from pytex.interface.tex import TeX
from pytex.registry import Registry

_HSRT_HYPER_OPTS: Final[dict[str, str]] = {
    "pdfpagemode": "UseOutlines",
    "bookmarksopen": "true",
    "bookmarksopenlevel": "0",
    "hypertexnames": "false",
    "colorlinks": "true",
    "citecolor": "[rgb]{0.286, 0.427, 0.537}",
    "linkcolor": "[rgb]{0.161, 0.31, 0.427}",
    "urlcolor": "[rgb]{0.071, 0.212, 0.322}",
    "pdfstartview": "FitV",
    "unicode": "",
    "breaklinks": "true",
}


@Registry.add
def HSRTHyperref() -> TeX:
    """Hypersetup with HSRT brand colors (blue-gray citations, dark blue links)."""
    return Hypersetup(_HSRT_HYPER_OPTS)
