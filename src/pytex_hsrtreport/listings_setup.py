"""HSRT listing styles and the captioned, boxed ``blstlisting`` environment.

Per-language ``\\lstset``/``\\lstdefinestyle`` calls are emitted as native
Python objects; the expl3 ``blstlisting`` environment definition lives in
``tex/listings_boxed.tex``.
"""

from pathlib import Path

from pytex import BuiltinPackages, IncludeTeX, Package, TeX
from pytex.library.listings import LstDefineStyle, LstSet
from pytex_komascript.model import Block

from .colors import DefineColor

_TEX_DIR = Path(__file__).parent / "tex"


_BASE_LSTSET: dict[str, object] = {
    "basicstyle": "\\footnotesize\\ttfamily",
    "breaklines": True,
    "numbers": "left",
    "frame": "single",
    "float": "H",
}


def _style(
    *,
    language: str,
    basicstyle: str = "\\footnotesize\\ttfamily",
    deletekeywords: str | None = None,
    morekeywords: str | None = None,
    numbers: str | None = None,
) -> dict[str, object]:
    opts: dict[str, object] = {
        "language": language,
        "basicstyle": basicstyle,
        "keywordstyle": "\\color{blue}\\bfseries\\ttfamily",
        "commentstyle": "\\color{gray}\\ttfamily",
        "escapechar": "|",
    }
    if deletekeywords is not None:
        opts["deletekeywords"] = deletekeywords
    if morekeywords is not None:
        opts["morekeywords"] = morekeywords
    if numbers is not None:
        opts["numbers"] = numbers
    return opts


def listings_setup_block() -> TeX:
    """Native ``\\lstset``/``\\lstdefinestyle`` calls + boxed env definition."""
    return Block(
        LstSet(_BASE_LSTSET),
        LstDefineStyle(
            "htmlCode",
            _style(language="html", basicstyle="\\scriptsize\\ttfamily"),
        ),
        LstDefineStyle(
            "phpCode",
            _style(language="php", morekeywords="{php}"),
        ),
        LstDefineStyle(
            "jsCode",
            _style(
                language="javascript",
                basicstyle="\\scriptsize\\ttfamily",
                morekeywords="",
            ),
        ),
        LstDefineStyle(
            "shellCodeNOPASSWD",
            _style(
                language="sh",
                basicstyle="\\scriptsize\\ttfamily",
                deletekeywords="{for,kill,cat}",
                morekeywords="{sudo}",
                numbers="none",
            ),
        ),
        LstDefineStyle(
            "shellCode",
            _style(
                language="sh",
                basicstyle="\\scriptsize\\ttfamily",
                deletekeywords="{}",
                morekeywords="{sudo,chmod,chown,cp,su,rm,python}",
            ),
        ),
        LstDefineStyle(
            "URL",
            {
                "basicstyle": "\\footnotesize\\ttfamily",
                "commentstyle": "\\color{gray}\\ttfamily",
                "escapechar": "|",
                "numbers": "none",
            },
        ),
        DefineColor("light-gray", "0.80", model="gray"),
        IncludeTeX(_TEX_DIR / "listings_boxed.tex"),
    )


def listings_packages() -> set[Package | str]:
    return {
        BuiltinPackages.LISTINGS.value,
        BuiltinPackages.XCOLOR.value,
        BuiltinPackages.HYPHENAT.value,
    }
