"""Bibliography setup — biblatex package + cite-command definitions.

``biblatex`` is added to the package list as a :class:`Package` whose
``options`` carry the backend/sorting/style/citestyle from the Python caller.
The HSRT-specific DeclareCiteCommand / DeclareFieldFormat / DeclareNameAlias
incantations are all native pytex nodes; no ``.tex`` asset.
"""

from typing import Literal

from pytex import (
    AddBibResource,
    BuiltinPackages,
    Command,
    DeclareCiteCommand,
    DeclareFieldFormat,
    DeclareNameAlias,
    ExecuteBibliographyOptions,
    Label,
    NewCommand,
    Package,
    RenewCommand,
    SetLength,
    TeX,
)
from pytex_komascript.model import Block

type Backend = Literal["bibtex", "biber"]


def BiblatexPackage(
    backend: Backend = "bibtex",
    style: str = "ieee",
    citestyle: str = "numeric",
    sorting: str = "nyt",
) -> Package:
    """Return the biblatex Package with the requested options."""
    opts = f"backend={backend},sorting={sorting},style={style},citestyle={citestyle}"
    return Package(name="biblatex", options=opts)


def _CiteCommands() -> TeX:
    """The HSRT cite-command family with hyperref wrapping."""
    loop = "\\bibhyperref{\\usebibmacro{citeindex}\\usebibmacro{cite}}"
    textcite_loop = (
        "\\bibhyperref{\\usebibmacro{citeindex}\\printnames{labelname}"
        "\\setunit{\\nameyeardelim}\\printfield{year}}"
    )
    return Block(
        DeclareCiteCommand(
            "cite",
            "\\usebibmacro{prenote}",
            loop,
            "\\multicitedelim",
            "\\usebibmacro{postnote}",
        ),
        DeclareCiteCommand(
            "parencite",
            "\\usebibmacro{prenote}",
            loop,
            "\\multicitedelim",
            "\\usebibmacro{postnote}",
            wrapper="\\mkbibparens",
        ),
        DeclareCiteCommand(
            "textcite",
            "\\usebibmacro{prenote}",
            textcite_loop,
            "\\multicitedelim",
            "\\usebibmacro{postnote}",
        ),
        NewCommand(
            "fcite",
            "\\hyperlink{cite.#1}{\\citeauthor{#1}, \\citeyear{#1}}",
            n_args=1,
        ),
        DeclareCiteCommand(
            "footcite",
            "\\usebibmacro{prenote}",
            loop,
            "\\multicitedelim",
            "\\usebibmacro{postnote}",
            wrapper="\\mkbibfootnote",
        ),
    )


def BibliographyBlock() -> TeX:
    """HSRT-customised biblatex declarations, native."""
    return Block(
        ExecuteBibliographyOptions(
            "hyperref=true,backref=false,url=true,doi=true,isbn=false"
        ),
        DeclareFieldFormat("citehyperref", "\\bibhyperref{#1}"),
        _CiteCommands(),
        RenewCommand("nameyeardelim", "\\addcomma\\space"),
        RenewCommand("multicitedelim", "\\addsemicolon\\space"),
        DeclareNameAlias("sortname", "family-given"),
        DeclareNameAlias("default", "given-family"),
        DeclareFieldFormat("url", "\\url{#1}"),
        DeclareFieldFormat(
            "doi",
            (
                "\\ifhyperref{\\href{https://doi.org/#1}{\\nolinkurl{doi:#1}}}"
                + "{\\nolinkurl{doi:#1}}"
            ),
        ),
        SetLength("bibitemsep", "0.5\\baselineskip"),
        SetLength("bibhang", "2em"),
    )


def AddBibResourceCmd(path: str) -> TeX:
    """``\\addbibresource{path}``."""
    return AddBibResource(path)


def MakebibCommand() -> TeX:
    """``\\newcommand{\\makebib}{...}`` — used at end of document.

    Uses ``Command("printbibliography", ...)`` rather than
    :class:`pytex.PrintBibliography` so the macro definition does not pull
    biblatex into the package list of documents that never bind a bib.
    """
    return NewCommand(
        "makebib",
        Block(
            Command("clearpage"),
            Command("chapter*", "Literaturverzeichnis"),
            Label("chap:bibliography"),
            Command("printbibliography", options="heading=none,title={}"),
        ),
    )


def BibliographyPackages() -> set[Package | str]:
    return {BuiltinPackages.CSQUOTES.value}


__all__ = [
    "Backend",
    "BiblatexPackage",
    "BibliographyBlock",
    "AddBibResourceCmd",
    "MakebibCommand",
    "BibliographyPackages",
]
