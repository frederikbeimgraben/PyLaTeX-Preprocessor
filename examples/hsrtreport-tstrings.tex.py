"""`.tex.py` example: `hsrtreport.tex.py` rebuilt with t-string templates.

    pytex examples/hsrtreport-tstrings.tex.py --build

Same document as `hsrtreport.tex.py`, but the prose-heavy parts (abstract and
body) are written with `tex(t"...")` instead of `Concat(...)`: the running text
is literal, and the boxes / sections / citations / math are spliced in as
interpolations. Needs Python 3.14 (or a prebuilt pytex binary). Compiling needs
`biber` and `makeindex`, run automatically by tectonic.
"""

from pytex import tex
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
_BIB = r"""\begin{filecontents}[noheader]{\jobname.bib}
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

# Preamble is all factory calls (no prose), so t-strings buy nothing here.
_PREAMBLE = Concat(
    WatermarkCounter(),
    DraftWatermark("ENTWURF"),
    WordcountCommands(),
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
    Newacronym("hsrt", "HSRT", "Hochschule Reutlingen"),
    Newacronym("inf", "INF", "Fakultät Informatik"),
    Raw(_BIB),
    Addbibresource(r"\jobname.bib"),
)

# Nested nodes pre-built so the big body template stays flat and readable.
_NESTED_WARNING = WarningBox(
    tex(t"Be careful here.{InfoBox('Boxes nest, with a darker background per level.')}")
)
_FOOTNOTE = Footnote(tex(t"See also {Parencite('knuth1984texbook')}."))
_QUADRATIC = DisplayMath(tex(t"x = {Frac('-b', '2a')}"))
_KEPT = Keeptogether(
    "This paragraph is kept together on one page via Keeptogether. "
    "Useful for short blocks that must not split."
)

__pytex__ = HSRTReport(
    variant=Variant.INF,
    show_toc=True,
    show_titlepage=True,
    show_glossary=True,
    show_acronyms=True,
    show_bibliography=True,
    show_footer_logos=True,
    inline_logos=True,
    inline_fonts=True,
    title="HSRT Report — Feature Demo (t-strings)",
    author="PyTeX",
    abstract=tex(
        t"This report builds with every {Gls('pytex')} feature enabled so a "
        t"single compile smoke-tests the whole package: title page, table of "
        t"contents, glossary, acronyms, bibliography and footer logos."
    ),
    keywords="PyTeX, LaTeX, HSRT, Demo",
    data_lines=(
        TitlePageDataLine("Autor", "PyTeX"),
        TitlePageDataLine("Fakultät", Acrlong("inf")),
        TitlePageDataLine("Datum", "2026-06-01"),
    ),
    user_preamble=_PREAMBLE,
    body=tex(t"""{Chapter("Callout boxes")}{Label("chap:boxes")}
The HSRT callouts render as nestable colored boxes:
{InfoBox("An informational note.")}
{SuccessBox("Something went well.")}
{ImportantBox("Worth remembering.")}
{_NESTED_WARNING}
{CustomBox("A custom box with a chosen icon and colour.", "rocket", "navyblue")}
{DiscussionBox("An open question for discussion.")}
{Chapter("Terminology and sources")}
A {Gls("preprocessor")} rewrites source before compilation. {Glspl("pytex")} documents are built from Python objects.
{Section("Acronyms")}
Short form: {Acrshort("hsrt")}. Long form: {Acrlong("hsrt")}. Full form: {Acrfull("inf")}.
{Section("Citations")}
Textual: {Textcite("knuth1984texbook")}. Parenthetical: {Parencite("lamport1994latex")}. Auto: {Autocite("knuth1984texbook")}. Inline link: {Fcite("lamport1994latex")}.{_FOOTNOTE}
{Nocite("*")}
{Chapter("Math, lists and voting")}
{Smartsection("Math and lists", "Math/lists")}
Inline math like {Math("a^2 + b^2 = c^2")} works as usual:
{_QUADRATIC}
{Enumerate("first point", "second point", "third point")}
{Itemize("bullet one", "bullet two")}
{Quote("A short block quotation, set apart from the body text.")}
{Subsection("Voting result")}
{VotingResults(yes=12, no=3, abstain=2, body="Motion to adopt PyTeX:")}
{Subsection("Page-break helpers")}
{_KEPT}
{Raw(r"\par")}
{Critical("Critical content that should stay on the current page if possible.")}
"""),
)
