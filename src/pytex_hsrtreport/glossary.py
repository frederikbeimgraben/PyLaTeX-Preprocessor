from pytex.commands.glossaries import (
    Glsenablehyper,
    Makeglossaries,
    Setglossarystyle,
)
from pytex.interface.tex import TeX
from pytex.model.concat import Concat
from pytex.model.raw import Raw
from pytex.registry import Registry

__all__ = ["AcrShortcut", "HSRTGlossarySetup"]

# Custom L/C/R column types used by the manualfixedwidth glossary style. Each
# fixes a horizontal alignment while still allowing manual \newline breaks.
COLUMN_TYPES = (
    r"\newcolumntype{L}[1]{>{\raggedright\let\newline\\\arraybackslash\hspace{0pt}}p{#1}}"
    + r"\newcolumntype{C}[1]{>{\centering\let\newline\\\arraybackslash\hspace{0pt}}p{#1}}"
    + r"\newcolumntype{R}[1]{>{\raggedleft\let\newline\\\arraybackslash\hspace{0pt}}p{#1}}"
)

# A three-column glossary style with fixed widths (30%/58%/10% of \textwidth).
GLOSSARY_STYLE = (
    r"\newglossarystyle{manualfixedwidth}{"
    + r"\setglossarystyle{long3colheader}"
    + r"\renewenvironment{theglossary}{\begin{longtable}{@{}"
    + r"L{\dimexpr0.30\textwidth-\tabcolsep\relax}"
    + r" p{\dimexpr0.58\textwidth-\tabcolsep\relax}"
    + r" L{\dimexpr0.10\textwidth-\tabcolsep\relax}@{}}}{\end{longtable}}"
    + r"\renewcommand*{\glsgroupskip}{}"
    + r"\renewcommand{\arraystretch}{1.1}}"
)

# German column/section labels for the glossary and acronym lists.
GLOSSARY_LABELS = (
    r"\renewcommand*{\entryname}{Wort/Abkürzung}"
    + r"\renewcommand*{\descriptionname}{Bedeutung}"
    + r"\renewcommand*{\pagelistname}{Seite(n)}"
    + r"\renewcommand{\acronymname}{Abkürzungsverzeichnis}"
)


@Registry.add
def HSRTGlossarySetup() -> TeX:
    """Standard HSRT glossary setup.

    makeglossaries, manualfixedwidth style, German labels.
    """
    return Concat(
        Makeglossaries(),
        Raw(COLUMN_TYPES),
        Raw(GLOSSARY_STYLE),
        Setglossarystyle("manualfixedwidth"),
        Glsenablehyper(),
        Raw(GLOSSARY_LABELS),
    )


@Registry.add
def AcrShortcut() -> TeX:
    """Shortcut: `\\acr` aliases `\\acrshort`."""
    return Raw(r"\newcommand{\acr}{\acrshort}")
