"""`.tex.py` kitchen-sink example: a Reutlingen University (HSRT) report.

    pytex examples/hsrtreport.tex.py --build   # -> build/hsrtreport.out.pdf

Exercises *every* `HSRTReport` flag (title page, ToC, glossary, acronyms,
bibliography, footer logos) plus the bundled components (callout boxes, voting
tally, citations, watermark, smart sections, page-break helpers) so a single
build smoke-tests the whole package.

Compiling needs `biber` (biblatex) and `makeindex` (glossaries); tectonic runs
both automatically. The bibliography is embedded via `filecontents`, so no
external `.bib` file is required.
"""

from pytex.commands.biblatex import (
    Addbibresource,
    Autocite,
    Nocite,
    Parencite,
    Textcite,
)
from pytex.commands.builtin import (
    Chapter,
    Enumerate,
    Footnote,
    Itemize,
    Label,
    Quote,
    Section,
    Subsection,
)
from pytex.commands.glossaries import (
    Acrfull,
    Acrlong,
    Acrshort,
    Gls,
    Glspl,
    Newacronym,
    Newglossaryentry,
)
from pytex.model.concat import Concat
from pytex.model.math import DisplayMath, Frac, Math
from pytex.model.raw import Raw
from pytex_hsrtreport import (
    Critical,
    CustomBox,
    DiscussionBox,
    DraftWatermark,
    Fcite,
    HSRTReport,
    ImportantBox,
    InfoBox,
    Keeptogether,
    Smartsection,
    SuccessBox,
    Variant,
    VotingResults,
    WarningBox,
    WatermarkCounter,
    WordcountCommands,
)
from pytex_hsrtreport.titlepage import TitlePageDataLine

# -- Embedded bibliography (filecontents -> \jobname.bib, read by biber) -------
_BIB = r"""\begin{filecontents}[overwrite]{\jobname.bib}
@book{knuth1984texbook,
  author    = {Knuth, Donald E.},
  title     = {The {\TeX}book},
  year      = {1984},
  publisher = {Addison-Wesley},
}
@book{lamport1994latex,
  author    = {Lamport, Leslie},
  title     = {{\LaTeX}: A Document Preparation System},
  year      = {1994},
  publisher = {Addison-Wesley},
}
\end{filecontents}
"""

# -- Preamble: watermark, wordcount macros, glossary/acronym entries, bib ------
_PREAMBLE = Concat(
    # Draft watermark tiled across every page (declares the `it` counter first).
    WatermarkCounter(),
    DraftWatermark("ENTWURF"),
    # \quickwordcount / \detailtexcount macros (defined only; need texcount).
    WordcountCommands(),
    # Glossary terms (used via \gls in the body, printed in the back matter).
    Newglossaryentry(
        "preprocessor",
        {
            "name": "Präprozessor",
            "description": "Programm, das Quelltext vor dem eigentlichen "
            + "Übersetzen transformiert",
        },
    ),
    Newglossaryentry(
        "pytex",
        {
            "name": "PyTeX",
            "description": "Python-Präprozessor, der TeX-Quelltext aus "
            + "Python-Objekten erzeugt",
        },
    ),
    # Acronyms (used via \acrshort / \acrlong / \acrfull).
    Newacronym("hsrt", "HSRT", "Hochschule Reutlingen"),
    Newacronym("inf", "INF", "Fakultät Informatik"),
    # Bibliography resource.
    Raw(_BIB),
    Addbibresource(r"\jobname.bib"),
)

__pytex__ = HSRTReport(
    # -- every flag on ---------------------------------------------------------
    variant=Variant.INF,
    show_toc=True,
    show_titlepage=True,
    show_glossary=True,
    show_acronyms=True,
    show_bibliography=True,
    show_footer_logos=True,
    inline_logos=True,
    inline_fonts=True,
    # -- title-page metadata ---------------------------------------------------
    title="HSRT Report — Feature Demo",
    author="PyTeX",
    abstract=Concat(
        "This report builds with every ",
        Gls("pytex"),
        " feature enabled so a single compile smoke-tests the whole package: "
        + "title page, table of contents, glossary, acronyms, bibliography and "
        + "footer logos.",
    ),
    keywords="PyTeX, LaTeX, HSRT, Demo",
    data_lines=(
        TitlePageDataLine("Autor", "PyTeX"),
        TitlePageDataLine("Fakultät", Acrlong("inf")),
        TitlePageDataLine("Datum", "2026-06-01"),
    ),
    user_preamble=_PREAMBLE,
    body=Concat(
        # -- Chapter 1: callout boxes -----------------------------------------
        Chapter("Callout boxes"),
        Label("chap:boxes"),
        "The HSRT callouts render as nestable colored boxes:",
        InfoBox("An informational note."),
        SuccessBox("Something went well."),
        ImportantBox("Worth remembering."),
        WarningBox(
            Concat(
                "Be careful here.",
                InfoBox("Boxes nest, with a darker background per level."),
            )
        ),
        CustomBox("A custom box with a chosen icon and colour.", "rocket", "navyblue"),
        DiscussionBox("An open question for discussion."),
        # -- Chapter 2: glossary, acronyms, citations -------------------------
        Chapter("Terminology and sources"),
        "A ",
        Gls("preprocessor"),
        " rewrites source before compilation. ",
        Glspl("pytex"),
        " documents are built from Python objects.",
        Section("Acronyms"),
        Concat(
            "Short form: ",
            Acrshort("hsrt"),
            ". Long form: ",
            Acrlong("hsrt"),
            ". Full form: ",
            Acrfull("inf"),
            ".",
        ),
        Section("Citations"),
        Concat(
            "Textual: ",
            Textcite("knuth1984texbook"),
            ". ",
            "Parenthetical: ",
            Parencite("lamport1994latex"),
            ". ",
            "Auto: ",
            Autocite("knuth1984texbook"),
            ". ",
            "Inline link: ",
            Fcite("lamport1994latex"),
            ".",
        ),
        Footnote(Concat("See also ", Parencite("knuth1984texbook"), ".")),
        # Pull both entries into the bibliography even if not all are cited.
        Nocite("*"),
        # -- Chapter 3: math, lists, voting -----------------------------------
        Chapter("Math, lists and voting"),
        Smartsection("Math and lists", "Math/lists"),
        Concat("Inline math like ", Math("a^2 + b^2 = c^2"), " works as usual:"),
        DisplayMath(Concat("x = ", Frac("-b", "2a"))),
        Enumerate("first point", "second point", "third point"),
        Itemize("bullet one", "bullet two"),
        Quote("A short block quotation, set apart from the body text."),
        Subsection("Voting result"),
        VotingResults(yes=12, no=3, abstain=2, body="Motion to adopt PyTeX:"),
        # -- page-break helpers ------------------------------------------------
        # Keeptogether wraps a \linewidth minipage, so it needs its own
        # paragraph; \par before and after keeps it in vertical mode.
        Subsection("Page-break helpers"),
        Keeptogether(
            Concat(
                "This paragraph is kept together on one page via Keeptogether. ",
                "Useful for short blocks that must not split.",
            )
        ),
        Raw(r"\par"),
        Critical("Critical content that should stay on the current page if possible."),
    ),
)
