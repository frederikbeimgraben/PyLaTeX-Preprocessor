from pytex.interface.tex import TeX
from pytex.model.raw import Raw
from pytex.registry import Registry

_SETUP = r"""
\makeatletter
\def\@title{}
\def\@author{}
\newif\ifHSRTBackMatter
\newif\ifHSRTTitlePage
\providecommand{\blenderfont}{\sffamily}
\providecommand{\dinfont}{\rmfamily}
\let\Chaptermark\chaptermark
\def\chaptermark#1{\def\Chaptername{#1}\Chaptermark{#1}}
\let\Sectionmark\sectionmark
\def\sectionmark#1{\def\Sectionname{#1}\Sectionmark{#1}}
\AtEndDocument{\immediate\write\@auxout{\string\gdef\string\@lastpage{\thepage}}}
\clearpairofpagestyles
\setkomafont{pageheadfoot}{\color{gray}\blenderfont}
\setkomafont{pagenumber}{\color{gray}\blenderfont}
\setlength{\footskip}{35pt}
\ohead*{\ifHSRTBackMatter\else\ifnum\value{chapter}>0\relax\Roman{\thechapter}~–~\Chaptername\fi\fi}
\ifoot{\@author}
\cfoot{\ifHSRTBackMatter\else Seite~\thepage\if@mainmatter\@ifundefined{@lastpage}{}{~von~\@lastpage}\fi\fi}
\ohead{\ifHSRTBackMatter\else\ifnum\value{chapter}>0\relax\thechapter~–~\Chaptername\fi\fi}
\ihead{\@title}
\pagestyle{scrheadings}
\renewcommand*{\chapterpagestyle}{scrheadings}
\setkomafont{disposition}{\blenderfont\bfseries}
\setkomafont{chapter}{\LARGE\blenderfont\bfseries}
\setkomafont{section}{\Large\blenderfont\bfseries}
\setkomafont{subsection}{\large\blenderfont\bfseries}
\setkomafont{subsubsection}{\large\blenderfont\bfseries}
\RedeclareSectionCommand[beforeskip=3ex plus 1ex minus 0.5ex,afterskip=1.5ex plus 0.3ex,style=section]{chapter}
\RedeclareSectionCommand[beforeskip=4.5ex plus 1.5ex minus 0.5ex,afterskip=1.5ex plus 0.3ex]{section}
\RedeclareSectionCommand[beforeskip=3.5ex plus 1ex minus 0.5ex,afterskip=1ex plus 0.2ex]{subsection}
\RedeclareSectionCommand[beforeskip=2ex plus 0.5ex minus 0.3ex,afterskip=0.8ex plus 0.1ex]{subsubsection}
\counterwithin{figure}{chapter}
\counterwithin{table}{chapter}
\counterwithout{equation}{chapter}
\renewcommand{\thefigure}{\thechapter.\arabic{figure}}
\renewcommand{\thetable}{\thechapter.\arabic{table}}
\renewcommand{\baselinestretch}{1.5}
\hyphenpenalty=500
\exhyphenpenalty=500
\tolerance=1000
\emergencystretch=3em
\widowpenalty=10000
\clubpenalty=10000
\raggedbottom
\setlength{\parskip}{0.5em plus 0.2em minus 0.1em}
\setlength{\parindent}{0pt}
% Prevent \mainmatter from inserting a blank page via \cleardoublepage.
% scrbook's \mainmatter calls \cleardoublepage to force chapters onto a
% right-hand page; for single-sided reports that just produces an unwanted
% blank page between the ToC and the first chapter.
\renewcommand{\mainmatter}{%
  \clearpage
  \@mainmattertrue
  \pagenumbering{arabic}%
}
% \baselinestretch=1.5 changes \baselineskip *after* typearea computed the type
% area for single spacing, leaving \textheight off the line grid (overfull \vbox
% "while \output is active" on every page). Recompute the type area once the
% stretched \baselineskip is live, at begin-document.
\AtBeginDocument{\recalctypearea}
\makeatother
"""


@Registry.add
def HSRTPageSetup() -> TeX:
    """KOMA scrheadings, section fonts, chapter-name tracking, typography.

    Mirrors ``Config/PageSetup.tex``, ``Config/Sections.tex``, and
    ``Config/Typography.tex`` from the original HSRTReport template.

    Must be emitted in the preamble *before* font setup: the ``\\providecommand``
    fallbacks here define ``\\blenderfont``/``\\dinfont`` as safe defaults, and
    ``HSRTFontSetup`` then overrides them with ``\\renewcommand`` once the real
    font families are declared.

    Defines ``\\ifHSRTBackMatter`` — set it to true in back matter to suppress
    chapter-specific headers/footers without calling mode-sensitive KOMA commands.
    """
    return Raw(_SETUP, allow_replacements=False)
