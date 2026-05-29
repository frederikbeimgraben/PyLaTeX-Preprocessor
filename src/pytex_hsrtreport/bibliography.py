r"""Bibliography setup (faithful copy of ``Config/Bibliography.tex`` and
``Pages/Bibliography.tex``), with backend/style chosen from Python.
"""

from typing import Literal

type Backend = Literal["bibtex", "biber"]


def bibliography_config(
    backend: Backend = "bibtex",
    style: str = "ieee",
    citestyle: str = "numeric",
    sorting: str = "nyt",
) -> str:
    """biblatex load + HSRT citation formatting."""
    return (
        rf"\RequirePackage[backend={backend},sorting={sorting},style={style},citestyle={citestyle}]{{biblatex}}"
        "\n"
        r"""\RequirePackage{csquotes}
\ExecuteBibliographyOptions{hyperref=true,backref=false,url=true,doi=true,isbn=false}
\DeclareFieldFormat{citehyperref}{\bibhyperref{#1}}
\DeclareCiteCommand{\cite}{\usebibmacro{prenote}}{\bibhyperref{\usebibmacro{citeindex}\usebibmacro{cite}}}{\multicitedelim}{\usebibmacro{postnote}}
\DeclareCiteCommand{\parencite}[\mkbibparens]{\usebibmacro{prenote}}{\bibhyperref{\usebibmacro{citeindex}\usebibmacro{cite}}}{\multicitedelim}{\usebibmacro{postnote}}
\DeclareCiteCommand{\textcite}{\usebibmacro{prenote}}{\bibhyperref{\usebibmacro{citeindex}\printnames{labelname}\setunit{\nameyeardelim}\printfield{year}}}{\multicitedelim}{\usebibmacro{postnote}}
\newcommand{\fcite}[1]{\hyperlink{cite.#1}{\citeauthor{#1}, \citeyear{#1}}}
\DeclareCiteCommand{\footcite}[\mkbibfootnote]{\usebibmacro{prenote}}{\bibhyperref{\usebibmacro{citeindex}\usebibmacro{cite}}}{\multicitedelim}{\usebibmacro{postnote}}
\renewcommand{\nameyeardelim}{\addcomma\space}
\renewcommand{\multicitedelim}{\addsemicolon\space}
\DeclareNameAlias{sortname}{family-given}
\DeclareNameAlias{default}{given-family}
\DeclareFieldFormat{url}{\url{#1}}
\DeclareFieldFormat{doi}{\ifhyperref{\href{https://doi.org/#1}{\nolinkurl{doi:#1}}}{\nolinkurl{doi:#1}}}
\setlength{\bibitemsep}{0.5\baselineskip}
\setlength{\bibhang}{2em}
"""
    )


def add_bib_resource(path: str) -> str:
    """``\\addbibresource{path}``."""
    return f"\\addbibresource{{{path}}}"


# \makebib — printed at end of document.
MAKEBIB = r"""\newcommand{\makebib}{
  \clearpage
  \chapter*{Literaturverzeichnis}
  \label{chap:bibliography}
  \printbibliography[heading=none,title={}]
}"""
