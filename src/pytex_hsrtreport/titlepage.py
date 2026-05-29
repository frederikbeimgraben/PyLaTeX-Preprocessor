"""Title page builder — the ``\\maketitle`` redefinition is generated from
Python, with per-logo ``\\node`` lines baked in based on the resolved logo set.
"""

from pytex import RenewCommand, TeX
from pytex.model.raw import Raw, coerce_tex
from pytex_komascript.model import Block

from .logos import titlepage_logo_nodes

# Pre-logo top: heart-link + dummy ``logo0`` anchor.
_TITLEPAGE_HEAD = r"""\def\istitlepage=\true
\pagenumbering{arabic}
\providecommand{\titlepageabstract}{Dies ist ein Beispiel für ein Abstract.}
\providecommand{\titlepagekeywords}{Seminararbeit, Beispiel}
\setlength{\imageHeight}{2cm*\real{\mainLogoScale}*\real{\logosScale}}
\begin{titlepage}
  \begin{tikzpicture}[overlay, remember picture]
    \node[anchor=south east, inner sep=0pt, xshift=-0.1cm, yshift=0.1cm] (heart) at (current page.south east) {
      \href{https://github.com/frederikbeimgraben/HSRT-Report}{\tiny\color{gray}\blenderfont Made with {\ensuremath\heartsuit} in \LaTeX}
    };
    \node[anchor=north west, inner sep=0pt, xshift=\leftmargin, yshift=-1.5cm, opacity=0] (logo0) at (current page.north west) {
      \includegraphics[height=\imageHeight]{\imagesPath/DUMMY_FOOT.png}
    };
"""

# Post-logo: closing the tikzpicture and the rest of the title page.
_TITLEPAGE_TAIL = r"""    \end{tikzpicture}
    \vspace{4cm}
    \begin{flushleft}
      {\noindent\color{black}\textbf{\blenderfont\Huge\hspace*{-2.5pt}\@title}}
      \color{black}\vspace*{-0.5em}\rule{\textwidth}{0.5mm}
    \end{flushleft}
    \vspace{2em}\setstretch{1.0}
    \section*{Abstract}\vspace{-1em}\titlepageabstract
    {\vspace*{1em}\newline\textbf{Keywords}\newline\titlepagekeywords}
    \vfill\noindent\setstretch{1.0}
    \GetTitlePageDataTable
  \end{titlepage}
"""

# Title-page data-table machinery (token register based).
_DATA_TABLE_DEFS = r"""\newcommand{\createdon}[1]{\gdef\@createdon{#1}}
\newtoks\titlePageData
\def\tand{&}
\titlePageData={\tand}
\DeclareRobustCommand{\AddTitlePageDataSpace}[1]{\titlePageData=\expandafter{\the\titlePageData \vspace{#1}}}
\DeclareRobustCommand{\AddTitlePageDataLine}[2]{\titlePageData=\expandafter{\the\titlePageData\\ \textbf{#1}\tand #2}}
\DeclareRobustCommand{\GetTitlePageDataTable}{\begin{tabular}{@{} p{30mm} p{\textwidth-30mm-2\tabcolsep}}\the\titlePageData\end{tabular}}
"""


def title_page_defs(resolved: list[tuple[str, float]]) -> TeX:
    """Data-table machinery + ``\\renewcommand{\\maketitle}{...}``.

    Combines a token-register data-table block, a static title-page TikZ shell
    and the per-logo nodes baked from Python into a single ``\\makeatletter``-
    wrapped Raw. ``@``-letter internals and the tikz overlay are inseparable
    in TeX, so we ship them as one Raw rather than splitting into many TeX
    nodes that would not serialise into the right adjacency.
    """
    logo_block = titlepage_logo_nodes(resolved).serialize()
    maketitle_body = f"{_TITLEPAGE_HEAD}{logo_block}\n{_TITLEPAGE_TAIL}"
    inner = RenewCommand("maketitle", Raw(maketitle_body, escape_spaces=False))
    body = (
        "\\makeatletter\n"
        f"{_DATA_TABLE_DEFS}"
        f"{inner.serialize()}\n"
        "\\makeatother"
    )
    return Raw(body, escape_spaces=False, safe=False)


def _content(value: TeX | str) -> str:
    return coerce_tex(value).serialize() if isinstance(value, TeX) else str(value)


def title_metadata_block(
    *,
    title: TeX | str | None,
    author: TeX | str | None,
    created_on: str | None,
    abstract: TeX | str | None,
    keywords: TeX | str | None,
    module_name: str | None,
    data_lines: "list[tuple[str, TeX | str]] | None",
) -> TeX:
    """Emit ``\\title`` / ``\\author`` / abstract / keywords + data lines.

    The output is a :class:`Block` of small :class:`Raw` lines — each metadata
    command is built independently so an absent field omits its line entirely.
    """
    lines: list[TeX] = []
    if title is not None:
        lines.append(Raw(f"\\title{{{_content(title)}}}", escape_spaces=False))
    if author is not None:
        lines.append(Raw(f"\\author{{{_content(author)}}}", escape_spaces=False))
    if created_on is not None:
        lines.append(Raw(f"\\createdon{{{created_on}}}", escape_spaces=False))
    if abstract is not None:
        lines.append(
            Raw(
                f"\\newcommand{{\\titlepageabstract}}{{{_content(abstract)}}}",
                escape_spaces=False,
            )
        )
    if keywords is not None:
        lines.append(
            Raw(
                f"\\newcommand{{\\titlepagekeywords}}{{{_content(keywords)}}}",
                escape_spaces=False,
            )
        )
    if module_name is not None:
        lines.append(
            Raw(
                f"\\newcommand{{\\modulename}}{{{module_name}}}",
                escape_spaces=False,
            )
        )
    for label, content in data_lines or []:
        lines.append(
            Raw(
                f"\\AddTitlePageDataLine{{{label}}}{{{_content(content)}}}",
                escape_spaces=False,
            )
        )
        lines.append(Raw("\\AddTitlePageDataSpace{5pt}", escape_spaces=False))
    return Block(*lines)


__all__ = [
    "title_page_defs",
    "title_metadata_block",
]
