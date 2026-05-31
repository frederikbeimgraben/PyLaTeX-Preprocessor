from typing import Final

from pytex.commands.listings import Lstdefinestyle, Lstset
from pytex.interface.tex import TeX
from pytex.model.concat import Concat
from pytex.registry import Registry

_BASE: Final[dict[str, str]] = {
    "basicstyle": r"\footnotesize\ttfamily",
    "breaklines": "true",
    "numbers": "left",
    "frame": "single",
    "float": "H",
}


_STYLES: Final[dict[str, dict[str, str]]] = {
    "htmlCode": {
        "language": "html",
        "basicstyle": r"\scriptsize\ttfamily",
        "keywordstyle": r"\color{blue}\bfseries\ttfamily",
        "commentstyle": r"\color{gray}\ttfamily",
        "escapechar": "|",
    },
    "phpCode": {
        "language": "php",
        "morekeywords": "{php}",
        "basicstyle": r"\footnotesize\ttfamily",
        "keywordstyle": r"\color{blue}\bfseries\ttfamily",
        "commentstyle": r"\color{gray}\ttfamily",
        "escapechar": "|",
    },
    "jsCode": {
        "language": "javascript",
        "basicstyle": r"\scriptsize\ttfamily",
        "keywordstyle": r"\color{blue}\bfseries\ttfamily",
        "commentstyle": r"\color{gray}\ttfamily",
        "escapechar": "|",
    },
    "shellCodeNOPASSWD": {
        "language": "sh",
        "deletekeywords": "{for,kill,cat}",
        "morekeywords": "{sudo}",
        "basicstyle": r"\scriptsize\ttfamily",
        "keywordstyle": r"\color{blue}\bfseries\ttfamily",
        "commentstyle": r"\color{gray}\ttfamily",
        "escapechar": "|",
        "numbers": "none",
    },
    "shellCode": {
        "language": "sh",
        "morekeywords": "{sudo,chmod,chown,cp,su,rm,python}",
        "basicstyle": r"\scriptsize\ttfamily",
        "keywordstyle": r"\color{blue}\bfseries\ttfamily",
        "commentstyle": r"\color{gray}\ttfamily",
        "escapechar": "|",
    },
    "URL": {
        "basicstyle": r"\footnotesize\ttfamily",
        "commentstyle": r"\color{gray}\ttfamily",
        "escapechar": "|",
        "numbers": "none",
    },
}


@Registry.add
def HSRTListingStyles() -> TeX:
    """All HSRT listing styles + global Lstset, emit once in preamble."""
    return Concat(
        Lstset(_BASE),
        *(Lstdefinestyle(name, opts) for name, opts in _STYLES.items()),
    )


def style_options(name: str) -> dict[str, str]:
    """Return raw option dict for a registered style (for adhoc rendering)."""
    return dict(_STYLES[name])
