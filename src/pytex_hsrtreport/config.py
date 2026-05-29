r"""Faithful copies of the HSRTReport class configuration modules.

Each constant reproduces the body of the corresponding ``Config/*.tex`` (or
``Imports.tex``) file from the original document class. They are emitted into the
preamble verbatim by :func:`pytex_hsrtreport.HSRTReport`. Blocks that use
``@``-letter internals are wrapped in ``\makeatletter`` / ``\makeatother`` by
``document.py``.
"""

# --- Imports.tex (core packages) -------------------------------------------
IMPORTS = r"""\usepackage[ngerman]{babel}
\RequirePackage[T1]{fontenc}
\RequirePackage[a4paper,top=2cm,bottom=2cm,left=2cm,right=2cm]{geometry}
\RequirePackage{calc}
\RequirePackage{xfp}
\RequirePackage{keyval}
\RequirePackage{ifthen}
\RequirePackage{etoolbox}
\RequirePackage{expl3}
\RequirePackage{l3keys2e}
\RequirePackage{pdftexcmds}
\RequirePackage{graphicx}
\RequirePackage{xcolor}
\RequirePackage{environ}
\RequirePackage{bophook}
\RequirePackage{arrayjobx}
\RequirePackage{lipsum}
\RequirePackage{tabularx}
\RequirePackage{longtable}
\RequirePackage{multirow}
\RequirePackage{arydshln}
\RequirePackage{array}
\RequirePackage{enumitem}
\RequirePackage{caption}
\RequirePackage[subrefformat=parens]{subcaption}
\RequirePackage{floatrow}
\RequirePackage{pifont}
\RequirePackage{fontawesome5}
\RequirePackage{tikz}
\RequirePackage{pgf}
\RequirePackage{pgffor}
\RequirePackage{chngcntr}
\RequirePackage{setspace}
\RequirePackage{accsupp}
\RequirePackage[framemethod=TikZ]{mdframed}
\RequirePackage{multicol}

% String comparison command (used internally by some helpers)
\ExplSyntaxOn
\cs_new_eq:NN \strcompare \str_if_eq:eeTF
\ExplSyntaxOff

% Fallback font commands; overridden in the fonts module
\providecommand{\blenderfont}{\sffamily}
\providecommand{\dinfont}{\rmfamily}
"""

# --- Config/Hyperref.tex ----------------------------------------------------
HYPERREF = r"""\RequirePackage{hyperref}
\hypersetup{
  pdfpagemode={UseOutlines},
  bookmarksopen=true,
  bookmarksopenlevel=0,
  hypertexnames=false,
  colorlinks=true,
  citecolor=[rgb]{0.286, 0.427, 0.537},
  linkcolor=[rgb]{0.161, 0.31, 0.427},
  urlcolor=[rgb]{0.071, 0.212, 0.322},
  pdfstartview={FitV},
  unicode,
  breaklinks=true
}
"""

# --- Config/Sections.tex (uses chaptermark hooks) ---------------------------
SECTIONS = r"""\RequirePackage{xcolor}
\setkomafont{disposition}{\blenderfont\bfseries}
\setkomafont{chapter}{\LARGE\blenderfont\bfseries}
\setkomafont{section}{\Large\blenderfont\bfseries}
\setkomafont{subsection}{\large\blenderfont\bfseries}
\setkomafont{subsubsection}{\large\blenderfont\bfseries}

\let\Chaptermark\chaptermark
\def\chaptermark#1{\def\Chaptername{#1}\Chaptermark{#1}}
\let\Sectionmark\sectionmark
\def\sectionmark#1{\def\Sectionname{#1}\Sectionmark{#1}}
\let\Subsectionmark\subsectionmark
\def\subsectionmark#1{\def\Subsectionname{#1}\Subsectionmark{#1}}
\let\Subsubsectionmark\subsubsectionmark
\def\subsubsectionmark#1{\def\Subsubsectionname{#1}\Subsubsectionmark{#1}}

\RedeclareSectionCommand[
  beforeskip=3ex plus 1ex minus 0.5ex,
  afterskip=1.5ex plus 0.3ex,
  style=section
]{chapter}
\RedeclareSectionCommand[
  beforeskip=4.5ex plus 1.5ex minus 0.5ex,
  afterskip=1.5ex plus 0.3ex,
]{section}
\RedeclareSectionCommand[
  beforeskip=3.5ex plus 1ex minus 0.5ex,
  afterskip=1ex plus 0.2ex,
]{subsection}
\RedeclareSectionCommand[
  beforeskip=2ex plus 0.5ex minus 0.3ex,
  afterskip=0.8ex plus 0.1ex,
]{subsubsection}

\setlength{\parskip}{0.8ex plus 0.2ex minus 0.1ex}
\newcommand{\decoRule}{\rule{.8\textwidth}{.4pt}}

\counterwithin{figure}{chapter}
\counterwithin{table}{chapter}
\counterwithout{equation}{chapter}
\renewcommand{\thefigure}{\thechapter.\arabic{figure}}
\renewcommand{\thetable}{\thechapter.\arabic{table}}
"""

# --- Config/Typography.tex (needs \makeatletter for @-penalties) ------------
TYPOGRAPHY = r"""\RequirePackage{listings}
\renewcommand{\baselinestretch}{1.5}
\hyphenpenalty=500
\exhyphenpenalty=500
\tolerance=1000
\emergencystretch=3em
\spaceskip=0.3em plus 0.2em minus 0.1em
\xspaceskip=0.6em plus 0.3em minus 0.15em
\widowpenalty=10000
\clubpenalty=10000
\displaywidowpenalty=10000
\@beginparpenalty=10000
\@endparpenalty=10000
\raggedbottom
\flushbottom
\interlinepenalty=150
\predisplaypenalty=10000
\postdisplaypenalty=10000
\floatingpenalty=20000
\setlength{\parskip}{0.5em plus 0.2em minus 0.1em}
\parfillskip=0pt plus 1fil
\setlength{\parindent}{0pt}
\lstset{
  float=H,
  belowskip=-0.5em plus 0.2em,
  aboveskip=0.5em plus 0.2em,
  keepspaces=true,
  breaklines=true
}
\newenvironment{protecteditemize}{%
  \begin{minipage}{\linewidth}\begin{itemize}}{%
  \end{itemize}\end{minipage}}
\newenvironment{protectedenumerate}{%
  \begin{minipage}{\linewidth}\begin{enumerate}}{%
  \end{enumerate}\end{minipage}}
\AtBeginEnvironment{itemize}{\nopagebreak[4]\interlinepenalty=5000}
\AtEndEnvironment{itemize}{\nopagebreak[3]}
\AtBeginEnvironment{enumerate}{\nopagebreak[4]\interlinepenalty=5000}
\AtEndEnvironment{enumerate}{\nopagebreak[3]}
\RequirePackage{needspace}
\RequirePackage{setspace}
\RequirePackage{ragged2e}
\renewcommand{\floatpagefraction}{0.8}
\renewcommand{\topfraction}{0.9}
\renewcommand{\bottomfraction}{0.9}
\renewcommand{\textfraction}{0.1}
\setcounter{topnumber}{2}
\setcounter{bottomnumber}{2}
\setcounter{totalnumber}{4}
\newenvironment{listenabsatz}{\begin{itemize}[nosep,leftmargin=*]}{\end{itemize}}
\newenvironment{listenabsatz*}{\begin{enumerate}[nosep,leftmargin=*]}{\end{enumerate}}
"""

# --- Config/PageBreakControl.tex --------------------------------------------
PAGEBREAKS = r"""\RequirePackage{needspace}
\RequirePackage{afterpage}
\RequirePackage{placeins}
\RequirePackage{etoolbox}
\RequirePackage{ifthen}
\RequirePackage{listings}
\binoppenalty=10000
\relpenalty=10000
\brokenpenalty=10000
\newlength{\sectionminspace}
\newlength{\subsectionminspace}
\newlength{\subsubsectionminspace}
\setlength{\sectionminspace}{12\baselineskip}
\setlength{\subsectionminspace}{10\baselineskip}
\setlength{\subsubsectionminspace}{8\baselineskip}
\pretocmd{\section}{\needspace{\sectionminspace}\FloatBarrier}{}{}
\pretocmd{\subsection}{\needspace{\subsectionminspace}}{}{}
\pretocmd{\subsubsection}{\needspace{\subsubsectionminspace}}{}{}
\newcommand{\keeptogether}[1]{\begin{minipage}{\linewidth}#1\end{minipage}}
\newcommand{\protectparagraph}{\nopagebreak[4]\interlinepenalty=10000}
\let\originallstlisting\lstlisting
\let\endoriginallstlisting\endlstlisting
\renewenvironment{lstlisting}[1][]{%
  \needspace{5\baselineskip}\nopagebreak[4]\originallstlisting[#1]}{%
  \endoriginallstlisting\nopagebreak[3]}
\AtBeginEnvironment{description}{\nopagebreak[4]\interlinepenalty=5000}
\AtEndEnvironment{description}{\nopagebreak[3]}
\AtBeginEnvironment{figure}{\nopagebreak[4]}
\AtEndEnvironment{figure}{\nopagebreak[3]}
\AtBeginEnvironment{table}{\nopagebreak[4]}
\AtEndEnvironment{table}{\nopagebreak[3]}
\AtBeginEnvironment{verbatim}{\nopagebreak[4]\interlinepenalty=10000}
\AtEndEnvironment{verbatim}{\nopagebreak[3]}
\AtBeginEnvironment{equation}{\nopagebreak[4]}
\AtEndEnvironment{equation}{\nopagebreak[3]}
\AtBeginEnvironment{align}{\nopagebreak[4]\interlinepenalty=10000}
\AtEndEnvironment{align}{\nopagebreak[3]}
\newcommand{\conditionalpagebreak}[1][10\baselineskip]{\needspace{#1}}
"""

# --- Config/ToC.tex (needs \makeatletter for \@dottedtocline) ---------------
TOC_CONFIG = r"""\RequirePackage{etoolbox}
\RequirePackage{listings}
\pretocmd{\addchaptertocentry}{\needspace{8\baselineskip}}{}{}
\apptocmd{\addchaptertocentry}{\nopagebreak[4]}{}{}
\AtBeginEnvironment{toc}{\clubpenalty=10000 \widowpenalty=10000 \interlinepenalty=500}
\RedeclareSectionCommand[tocbeforeskip=1.5em plus 0.5em]{chapter}
\RedeclareSectionCommands[
  tocentryformat=\blenderfont\normalsize,
  tocpagenumberformat=\blenderfont\normalsize,
]{section,subsection}
\pretocmd{\addsectiontocentry}{\penalty-500}{}{}
\pretocmd{\addsubsectiontocentry}{\nopagebreak[3]}{}{}
\renewcommand*{\l@lstlisting}[2]{\@dottedtocline{1}{1em}{2.3em}{\blenderfont#1}{\blenderfont#2}}
"""

# --- Config/CleverefNames.tex (German cref names) ---------------------------
CLEVEREF = r"""\RequirePackage{cleveref}
\crefname{figure}{Abbildung}{Abbildungen}
\Crefname{figure}{Abbildung}{Abbildungen}
\crefname{table}{Tabelle}{Tabellen}
\Crefname{table}{Tabelle}{Tabellen}
\crefname{equation}{Gleichung}{Gleichungen}
\Crefname{equation}{Gleichung}{Gleichungen}
\crefname{chapter}{Kapitel}{Kapitel}
\Crefname{chapter}{Kapitel}{Kapitel}
\crefname{section}{Abschnitt}{Abschnitte}
\Crefname{section}{Abschnitt}{Abschnitte}
\crefname{subsection}{Unterabschnitt}{Unterabschnitte}
\Crefname{subsection}{Unterabschnitt}{Unterabschnitte}
\crefname{subsubsection}{Unterunterabschnitt}{Unterunterabschnitte}
\Crefname{subsubsection}{Unterunterabschnitt}{Unterunterabschnitte}
\crefname{listing}{Listing}{Codeblock}
\Crefname{listing}{Listing}{Codeblock}
\crefname{appendix}{Anhang}{Anhänge}
\Crefname{appendix}{Anhang}{Anhänge}
\crefname{footnote}{Fußnote}{Fußnoten}
\Crefname{footnote}{Fußnote}{Fußnoten}
\crefname{enumi}{Punkt}{Punkte}
\Crefname{enumi}{Punkt}{Punkte}
\crefname{page}{Seite}{Seiten}
\Crefname{page}{Seite}{Seiten}
"""

# --- Config/GlossarySettings.tex --------------------------------------------
GLOSSARY_SETTINGS = r"""\RequirePackage[acronym, savenumberlist=true]{glossaries}
\RequirePackage{longtable}
\RequirePackage{array}
\RequirePackage{ragged2e}
\makeglossaries
\newcolumntype{L}[1]{>{\raggedright\let\newline\\\arraybackslash\hspace{0pt}}p{#1}}
\newcolumntype{C}[1]{>{\centering\let\newline\\\arraybackslash\hspace{0pt}}p{#1}}
\newcolumntype{R}[1]{>{\raggedleft\let\newline\\\arraybackslash\hspace{0pt}}p{#1}}
\newglossarystyle{manualfixedwidth}{
  \setglossarystyle{long3colheader}
  \renewenvironment{theglossary}
    {\begin{longtable}{@{} L{0.30\textwidth-\tabcolsep} p{0.58\textwidth-\tabcolsep} L{0.10\textwidth-\tabcolsep} @{}}}
    {\end{longtable}}
  \renewcommand*{\glsgroupskip}{}
  \renewcommand{\arraystretch}{1.1}
}
\setglossarystyle{manualfixedwidth}
\renewcommand*{\entryname}{Wort/Abkürzung}
\renewcommand*{\descriptionname}{Bedeutung}
\renewcommand*{\pagelistname}{Seite(n)}
\glsenablehyper
\renewcommand*{\glsclearpage}{}
\renewcommand{\acronymname}{Abkürzungsverzeichnis}
\glsaddkey{genitive}{}{\glsentrygenitive}{\Glsentrygenitive}{\glsgen}{\Glsgen}{\GLSgen}
\glsaddkey{dative}{}{\glsentrydative}{\Glsentrydative}{\glsdative}{\Glsdative}{\GLSdative}
\newcommand{\acr}{\acrshort}
"""

# --- Config/PageSetup.tex (needs \makeatletter for \@author / \@title) ------
PAGESETUP = r"""\RequirePackage{ifthen}
\RequirePackage{xcolor}
\RequirePackage{etoolbox}
\RequirePackage[singlespacing=true]{scrlayer-scrpage}
\clearpairofpagestyles
\AtEndDocument{\immediate\write\@auxout{\string\gdef\string\@lastpage{\thepage}}}
\setkomafont{pageheadfoot}{\color{gray}\blenderfont}
\setkomafont{pagenumber}{\color{gray}\blenderfont}
\setlength{\footskip}{35pt}
\ohead*{\ifnum\value{chapter}>0\relax \Roman{\thechapter}~–~\Chaptername \fi}
\ifoot{\@author}
\cfoot{\ifnum\value{chapter}>0\relax Seite~\thepage\@ifundefined{@lastpage}{}{~von~\@lastpage}\fi}
\ohead{\ifnum\value{chapter}>0\relax \thechapter~–~\Chaptername \fi}
\ihead{\@title}
\pagestyle{scrheadings}
"""
