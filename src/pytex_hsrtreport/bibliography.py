"""Bibliography setup — biblatex package + cite-command definitions.

``biblatex`` itself is added to the package list as a :class:`Package` whose
``options`` carry the backend/sorting/style/citestyle from the Python caller;
the DeclareCiteCommand declarations and a few setlength tweaks live in
``tex/bibliography.tex``.
"""

from pathlib import Path
from typing import Literal

from pytex import (
    BuiltinPackages,
    Command,
    IncludeTeX,
    NewCommand,
    Package,
    TeX,
)

_TEX_DIR = Path(__file__).parent / "tex"

type Backend = Literal["bibtex", "biber"]


def biblatex_package(
    backend: Backend = "bibtex",
    style: str = "ieee",
    citestyle: str = "numeric",
    sorting: str = "nyt",
) -> Package:
    """Return the biblatex Package with the requested options."""
    opts = f"backend={backend},sorting={sorting},style={style},citestyle={citestyle}"
    return Package(name="biblatex", options=opts)


def bibliography_block() -> TeX:
    """The HSRT-customised biblatex declarations (``tex/bibliography.tex``)."""
    return IncludeTeX(_TEX_DIR / "bibliography.tex")


def add_bib_resource(path: str) -> TeX:
    """``\\addbibresource{path}``."""
    return Command("addbibresource", path)


def makebib_command() -> TeX:
    """``\\newcommand{\\makebib}{...}`` — used at end of document."""
    return NewCommand(
        "makebib",
        "\\clearpage\n"
        + "\\chapter*{Literaturverzeichnis}\n"
        + "\\label{chap:bibliography}\n"
        + "\\printbibliography[heading=none,title={}]",
    )


def bibliography_packages() -> set[Package | str]:
    return {BuiltinPackages.CSQUOTES.value}


__all__ = [
    "Backend",
    "biblatex_package",
    "bibliography_block",
    "add_bib_resource",
    "makebib_command",
    "bibliography_packages",
]
