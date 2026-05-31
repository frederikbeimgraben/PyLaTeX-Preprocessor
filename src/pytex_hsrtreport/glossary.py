from pytex.commands.glossaries import (
    Glsenablehyper,
    Makeglossaries,
    Setglossarystyle,
)
from pytex.interface.tex import TeX
from pytex.model.concat import Concat
from pytex.model.raw import Raw
from pytex.registry import Registry


@Registry.add
def HSRTGlossarySetup() -> TeX:
    """Standard HSRT glossary setup: makeglossaries, manualfixedwidth style, German labels."""
    return Concat(
        Makeglossaries(),
        # Define custom column types L/C/R used by manualfixedwidth style
        Raw(
            r"\newcolumntype{L}[1]{>{\raggedright\let\newline\\\arraybackslash\hspace{0pt}}p{#1}}"
            + r"\newcolumntype{C}[1]{>{\centering\let\newline\\\arraybackslash\hspace{0pt}}p{#1}}"
            + r"\newcolumntype{R}[1]{>{\raggedleft\let\newline\\\arraybackslash\hspace{0pt}}p{#1}}"
        ),
        Raw(
            r"\newglossarystyle{manualfixedwidth}{"
            + r"\setglossarystyle{long3colheader}"
            + r"\renewenvironment{theglossary}{\begin{longtable}{@{}"
            + r"L{0.30\textwidth-\tabcolsep} p{0.58\textwidth-\tabcolsep}"
            + r" L{0.10\textwidth-\tabcolsep}@{}}}{\end{longtable}}"
            + r"\renewcommand*{\glsgroupskip}{}"
            + r"\renewcommand{\arraystretch}{1.1}}"
        ),
        Setglossarystyle("manualfixedwidth"),
        Glsenablehyper(),
        Raw(
            r"\renewcommand*{\entryname}{Wort/Abkürzung}"
            + r"\renewcommand*{\descriptionname}{Bedeutung}"
            + r"\renewcommand*{\pagelistname}{Seite(n)}"
            + r"\renewcommand{\acronymname}{Abkürzungsverzeichnis}"
        ),
    )


@Registry.add
def AcrShortcut() -> TeX:
    """Shortcut: `\\acr` aliases `\\acrshort`."""
    return Raw(r"\newcommand{\acr}{\acrshort}")
