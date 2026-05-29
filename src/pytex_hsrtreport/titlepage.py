r"""Title page (faithful copy of ``Pages/Titlepage.tex``) plus Python helpers
for the title-page data table, abstract and keywords (``Metadata.tex``).

Uses ``@``-letter internals, so it is emitted inside ``\makeatletter`` /
``\makeatother`` by ``document.py``.
"""

from pytex import TeX
from pytex.model.raw import coerce_tex

# Token-register data table machinery + \maketitle redefinition, verbatim.
TITLEPAGE_DEFS = r"""\newcommand{\createdon}[1]{\gdef\@createdon{#1}}
\newtoks\titlePageData
\def\tand{&}
\titlePageData={\tand}
\DeclareRobustCommand{\AddTitlePageDataSpace}[1]{\titlePageData=\expandafter{\the\titlePageData \vspace{#1}}}
\DeclareRobustCommand{\AddTitlePageDataLine}[2]{\titlePageData=\expandafter{\the\titlePageData\\ \textbf{#1}\tand #2}}
\DeclareRobustCommand{\GetTitlePageDataTable}{\begin{tabular}{@{} p{30mm} p{\textwidth-30mm-2\tabcolsep}}\the\titlePageData\end{tabular}}
\renewcommand{\maketitle}{
  \def\istitlepage=\true
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
      \foreach \i in {1,...,\value{logoCounter}} {
        \pgfmathtruncatemacro{\prev}{\i-1}
        \node[anchor=west, inner sep=0pt, xshift=0.5cm] (logo\i) at (logo\prev.east) {
          \makeatletter
          \testarray{LogosScales}(\i)
          \setlength{\imageHeight}{1.5cm*\real{\temp@macro}*\real{\logosScale}}
          \testarray{LogosPaths}(\i)
          \begin{tikzpicture}
            \node[] {\includegraphics[height=\imageHeight]{\logospath\temp@macro.pdf}};
          \end{tikzpicture}
          \makeatother
        };
      }
    \end{tikzpicture}
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
}
"""


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
) -> str:
    """Emit ``\\title``/``\\author``/abstract/keywords and title-page data lines."""
    parts: list[str] = []
    if title is not None:
        parts.append(f"\\title{{{_content(title)}}}")
    if author is not None:
        parts.append(f"\\author{{{_content(author)}}}")
    if created_on is not None:
        parts.append(f"\\createdon{{{created_on}}}")
    if abstract is not None:
        parts.append(f"\\newcommand{{\\titlepageabstract}}{{{_content(abstract)}}}")
    if keywords is not None:
        parts.append(f"\\newcommand{{\\titlepagekeywords}}{{{_content(keywords)}}}")
    if module_name is not None:
        parts.append(f"\\newcommand{{\\modulename}}{{{module_name}}}")
    for label, content in data_lines or []:
        parts.append(f"\\AddTitlePageDataLine{{{label}}}{{{_content(content)}}}")
        parts.append(r"\AddTitlePageDataSpace{5pt}")
    return "\n".join(parts)
