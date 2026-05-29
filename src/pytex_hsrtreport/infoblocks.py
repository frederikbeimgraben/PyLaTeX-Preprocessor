r"""Coloured callout boxes (faithful copy of ``Modules/Layout/InfoBlocks.tex``).

``INFOBLOCKS_PREAMBLE`` defines the LaTeX environments; the dataclasses below are
typed Python wrappers used to *emit* those environments in document content.
Colours are defined separately (see :mod:`pytex_hsrtreport.colors`).
"""

from dataclasses import dataclass
from typing import override

from pytex import Group, Package, TeX
from pytex.model.raw import coerce_tex

_REQUIRES: set[Package | str] = {"mdframed", "fontawesome5", "environ", "multicol"}

# The \NewEnviron definitions, verbatim from InfoBlocks.tex (colour \definecolor
# lines removed — they live in colors.py).
INFOBLOCKS_PREAMBLE = r"""\RequirePackage{xcolor}
\RequirePackage{fp}
\RequirePackage{environ}
\RequirePackage{mdframed}
\RequirePackage{fontawesome5}
\RequirePackage{keyval}
\RequirePackage{multicol}
\newcounter{coloredBoxLevel}
\makeatletter
\define@key{coloredBox}{icon}{\def\coloredBoxIcon{#1}}
\define@key{coloredBox}{icon.prefix}{\def\coloredBoxIconPrefix{#1}}
\define@key{coloredBox}{icon.fontsize}{\def\coloredBoxIconSize{#1}}
\define@key{coloredBox}{icon.offset.x}{\def\coloredBoxIconOffsetX{#1}}
\define@key{coloredBox}{icon.offset.y}{\def\coloredBoxIconOffsetY{#1}}
\define@key{coloredBox}{icon.color}{\def\coloredBoxColor{#1}}
\define@key{coloredBox}{background.color}{\def\coloredBoxBackground{#1}}
\makeatother
\NewEnviron{ColoredBox}[1][
   icon={\faInfoCircle}, icon.color={blue}, icon.prefix={},
   icon.fontsize={28pt}, icon.offset.x={0pt}, icon.offset.y={0pt},
   background.color={blue}
]{
   \setkeys{coloredBox}{#1}
   \stepcounter{coloredBoxLevel}
   \FPeval{\backgroundOpacityFloat}{0.05 + 0.075 * \arabic{coloredBoxLevel}}
   \FPeval{\backgroundOpacity}{round(\backgroundOpacityFloat * 100, 0)}
   \FPeval{\iconOpacity}{\backgroundOpacity + 20}
   \ifnum\value{coloredBoxLevel}=1 \filbreak \fi
   \vspace*{0.5\baselineskip}
   \noindent
   \begin{minipage}{\linewidth}
      \begin{mdframed}[
         backgroundcolor={\coloredBoxBackground!\backgroundOpacity},
         hidealllines=true, skipabove=0.7\baselineskip, skipbelow=0.7\baselineskip,
         splitbottomskip=2pt, splittopskip=4pt, roundcorner=5pt]
         \begin{picture}(\linewidth, 0)(0, 0)
            \put(\coloredBoxIconOffsetX-\coloredBoxIconSize,\coloredBoxIconOffsetY-0.7cm){
               \fontsize{\coloredBoxIconSize}{\coloredBoxIconSize}\selectfont
               \color{\coloredBoxColor!\iconOpacity} \coloredBoxIcon}
         \end{picture}
         \hspace*{0.25cm}
         \begin{minipage}{\linewidth-0.5cm}
            \vspace*{0.5\baselineskip}\BODY\vspace*{0.5\baselineskip}
         \end{minipage}
      \end{mdframed}
   \end{minipage}
   \addtocounter{coloredBoxLevel}{-1}
}
\NewEnviron{InfoBox}[1][icon={\faInfoCircle},icon.color={blue},icon.prefix={},icon.fontsize={24pt},icon.offset.x={0pt},icon.offset.y={0pt},background.color={blue}]{\let\iBODY\BODY\begin{ColoredBox}[#1]\iBODY\end{ColoredBox}}
\NewEnviron{WarningBox}[1][icon={\faExclamationTriangle},icon.color={red},icon.prefix={},icon.fontsize={24pt},icon.offset.x={0pt},icon.offset.y={0pt},background.color={red}]{\let\wBODY\BODY\begin{ColoredBox}[#1]\wBODY\end{ColoredBox}}
\NewEnviron{SuccessBox}[1][icon={\faCheckCircle},icon.color={green},icon.prefix={},icon.fontsize={24pt},icon.offset.x={0pt},icon.offset.y={2pt},background.color={green}]{\let\sBODY\BODY\begin{ColoredBox}[#1]\sBODY\end{ColoredBox}}
\NewEnviron{ImportantBox}[1][icon={\faExclamationCircle},icon.color={orange},icon.prefix={},icon.fontsize={24pt},icon.offset.x={0pt},icon.offset.y={0pt},background.color={orange}]{\let\impBODY\BODY\begin{ColoredBox}[#1]\impBODY\end{ColoredBox}}
\NewEnviron{CustomBox}[2]{\let\cBODY\BODY\begin{ColoredBox}[icon={#1},icon.color={#2},icon.prefix={},icon.fontsize={24pt},icon.offset.x={0pt},icon.offset.y={0pt},background.color={#2}]\cBODY\end{ColoredBox}}
\NewEnviron{VotingResultsBox}[1]{\let\VotingResultsBODY\BODY\begin{ColoredBox}[icon={\faVoteYea},icon.color={#1},icon.prefix={},icon.fontsize={24pt},icon.offset.x={-0.2cm},icon.offset.y={0pt},background.color={#1}]\VotingResultsBODY\end{ColoredBox}}
\NewEnviron{VotingResults}[3]{%
   \let\voteBODY\BODY
   \ifnum#1>#2 \def\voteColor{britishracinggreen}\else\ifnum#1<#2 \def\voteColor{red}\else\def\voteColor{eggplant}\fi\fi
   \begin{VotingResultsBox}{\voteColor}
      \voteBODY
      \par\medskip\noindent
      \begin{minipage}[t]{0.3\linewidth}\begin{CustomBox}{\faThumbsUp}{britishracinggreen}\textbf{Ja:} #1\end{CustomBox}\end{minipage}\hfill
      \begin{minipage}[t]{0.3\linewidth}\begin{CustomBox}{\faThumbsDown}{red}\textbf{Nein:} #2\end{CustomBox}\end{minipage}\hfill
      \begin{minipage}[t]{0.3\linewidth}\begin{CustomBox}{\faQuestion}{eggplant}\textbf{Enthaltung:} #3\end{CustomBox}\end{minipage}
   \end{VotingResultsBox}
}
\NewEnviron{DiscussionBox}[1][icon={\faComments},icon.color={hanblue},icon.prefix={},icon.fontsize={24pt},icon.offset.x={0pt},icon.offset.y={0pt},background.color={hanblue}]{\let\dBODY\BODY\begin{ColoredBox}[#1]\dBODY\end{ColoredBox}}
"""


@dataclass(init=False)
class _Box(TeX):
    """``\\begin{Name}[opts]{args} body \\end{Name}`` callout wrapper."""

    name: str
    body: TeX
    options: str | None
    args: tuple[str, ...]

    def __init__(
        self,
        name: str,
        body: TeX | str,
        *,
        options: str | None = None,
        args: tuple[str, ...] = (),
    ) -> None:
        self.name = name
        self.body = coerce_tex(body)
        self.options = options
        self.args = args

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return set(_REQUIRES)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.body,)

    @override
    def serialize(self) -> str:
        opt = f"[{self.options}]" if self.options is not None else ""
        args = "".join(f"{{{a}}}" for a in self.args)
        return (
            f"\\begin{{{self.name}}}{opt}{args}\n"
            f"{self.body.serialize()}\n"
            f"\\end{{{self.name}}}"
        )


def _simple_box(name: str):
    def make(*body: TeX | str, options: str | None = None) -> _Box:
        return _Box(name, Group(*body) if len(body) != 1 else body[0], options=options)

    return make


ColoredBox = _simple_box("ColoredBox")
InfoBox = _simple_box("InfoBox")
WarningBox = _simple_box("WarningBox")
SuccessBox = _simple_box("SuccessBox")
ImportantBox = _simple_box("ImportantBox")
DiscussionBox = _simple_box("DiscussionBox")


def CustomBox(body: TeX | str, icon: str, color: str) -> _Box:
    """``\\begin{CustomBox}{icon}{color} ... \\end{CustomBox}``."""
    return _Box("CustomBox", body, args=(icon, color))


def VotingResults(
    body: TeX | str, yes: int, no: int, abstain: int
) -> _Box:
    """``\\begin{VotingResults}{yes}{no}{abstain} ... \\end{VotingResults}``."""
    return _Box("VotingResults", body, args=(str(yes), str(no), str(abstain)))
