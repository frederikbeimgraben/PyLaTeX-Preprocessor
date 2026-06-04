from typing import Final

from pytex.commands.colors import SelectColor
from pytex.commands.font import (
    Bfseries,
    Ttfamily,
    footnotesize,
    scriptsize,
)
from pytex.commands.listings import Lstdefinestyle, Lstset
from pytex.interface.tex import TeX
from pytex.model.concat import Concat
from pytex.registry import Registry

__all__ = ["HSRTListingStyles", "style_options"]


def _font(*parts: TeX) -> TeX:
    return Concat(*parts)


HSRT_LISTING_BASE: Final[dict[str, TeX | str]] = {
    "basicstyle": _font(footnotesize(), Ttfamily()),
    "breaklines": "true",
    "numbers": "left",
    "frame": "single",
    "float": "H",
}


HSRT_LISTING_STYLES: Final[dict[str, dict[str, TeX | str]]] = {
    "htmlCode": {
        "language": "html",
        "basicstyle": _font(scriptsize(), Ttfamily()),
        "keywordstyle": _font(SelectColor("blue"), Bfseries(), Ttfamily()),
        "commentstyle": _font(SelectColor("gray"), Ttfamily()),
        "escapechar": "|",
    },
    "phpCode": {
        "language": "php",
        "morekeywords": "{php}",
        "basicstyle": _font(footnotesize(), Ttfamily()),
        "keywordstyle": _font(SelectColor("blue"), Bfseries(), Ttfamily()),
        "commentstyle": _font(SelectColor("gray"), Ttfamily()),
        "escapechar": "|",
    },
    "jsCode": {
        "language": "javascript",
        "basicstyle": _font(scriptsize(), Ttfamily()),
        "keywordstyle": _font(SelectColor("blue"), Bfseries(), Ttfamily()),
        "commentstyle": _font(SelectColor("gray"), Ttfamily()),
        "escapechar": "|",
    },
    "shellCodeNOPASSWD": {
        "language": "sh",
        "deletekeywords": "{for,kill,cat}",
        "morekeywords": "{sudo}",
        "basicstyle": _font(scriptsize(), Ttfamily()),
        "keywordstyle": _font(SelectColor("blue"), Bfseries(), Ttfamily()),
        "commentstyle": _font(SelectColor("gray"), Ttfamily()),
        "escapechar": "|",
        "numbers": "none",
    },
    "shellCode": {
        "language": "sh",
        "morekeywords": "{sudo,chmod,chown,cp,su,rm,python}",
        "basicstyle": _font(scriptsize(), Ttfamily()),
        "keywordstyle": _font(SelectColor("blue"), Bfseries(), Ttfamily()),
        "commentstyle": _font(SelectColor("gray"), Ttfamily()),
        "escapechar": "|",
    },
    "URL": {
        "basicstyle": _font(footnotesize(), Ttfamily()),
        "commentstyle": _font(SelectColor("gray"), Ttfamily()),
        "escapechar": "|",
        "numbers": "none",
    },
}


@Registry.add
def HSRTListingStyles() -> TeX:
    return Concat(
        Lstset(HSRT_LISTING_BASE),
        *(Lstdefinestyle(name, opts) for name, opts in HSRT_LISTING_STYLES.items()),
    )


def style_options(name: str) -> dict[str, TeX | str]:
    return dict(HSRT_LISTING_STYLES[name])
