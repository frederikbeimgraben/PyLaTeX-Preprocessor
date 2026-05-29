"""Native-pytex translations of the HSRTReport class configuration modules.

Each ``*_block()`` helper returns a :class:`pytex.TeX` node that emits the
corresponding ``Config/*.tex`` body. Static, hard-to-port fragments live as
``.tex`` files under :mod:`pytex_hsrtreport.tex`; the rest is built from
:mod:`pytex` natives (``\\setkomafont``, ``\\setlength``, ``\\newcommand``,
``\\renewcommand``, ``\\crefname``, ``\\hypersetup``, ...).
"""

from pathlib import Path

from pytex import (
    AtBeginDocument,
    AtEndDocument,
    BuiltinPackages,
    Command,
    CounterWithin,
    CounterWithout,
    Crefname,
    Hypersetup,
    IncludeTeX,
    NewCommand,
    NewLength,
    Package,
    ProvideCommand,
    RenewCommand,
    SetCounter,
    SetLength,
    TeX,
)
from pytex.library.listings import LstSet
from pytex.model.raw import Raw
from pytex_komascript import (
    Appendix,
    BackMatter,
    ClearPairOfPageStyles,
    FrontMatter,
    KomaOptions,
    MainMatter,
    Pagestyle,
    RedeclareSectionCommand,
    SetKomaFont,
)
from pytex_komascript.model import Block

_TEX_DIR = Path(__file__).parent / "tex"

#: Packages that the original ``Imports.tex`` pulled in.
IMPORTS_PACKAGES: set[Package | str] = {
    Package(name="babel", options="ngerman"),
    Package(name="fontenc", options="T1"),
    Package(name="geometry", options="a4paper,top=2cm,bottom=2cm,left=2cm,right=2cm"),
    BuiltinPackages.CALC.value,
    BuiltinPackages.XFP.value,
    BuiltinPackages.KEYVAL.value,
    BuiltinPackages.IFTHEN.value,
    BuiltinPackages.ETOOLBOX.value,
    BuiltinPackages.EXPL3.value,
    BuiltinPackages.L3KEYS2E.value,
    BuiltinPackages.PDFTEXCMDS.value,
    BuiltinPackages.GRAPHICX.value,
    BuiltinPackages.XCOLOR.value,
    BuiltinPackages.ENVIRON.value,
    BuiltinPackages.BOPHOOK.value,
    BuiltinPackages.ARRAYJOBX.value,
    BuiltinPackages.LIPSUM.value,
    BuiltinPackages.TABULARX.value,
    BuiltinPackages.LONGTABLE.value,
    BuiltinPackages.MULTIROW.value,
    BuiltinPackages.ARYDSHLN.value,
    BuiltinPackages.ARRAY.value,
    BuiltinPackages.ENUMITEM.value,
    BuiltinPackages.CAPTION.value,
    Package(name="subcaption", options="subrefformat=parens"),
    BuiltinPackages.FLOATROW.value,
    BuiltinPackages.PIFONT.value,
    BuiltinPackages.FONTAWESOME5.value,
    BuiltinPackages.TIKZ.value,
    BuiltinPackages.PGF.value,
    BuiltinPackages.PGFFOR.value,
    BuiltinPackages.CHNGCNTR.value,
    BuiltinPackages.SETSPACE.value,
    BuiltinPackages.ACCSUPP.value,
    Package(name="mdframed", options="framemethod=TikZ"),
    BuiltinPackages.MULTICOL.value,
    BuiltinPackages.HYPERREF.value,
    BuiltinPackages.LISTINGS.value,
    BuiltinPackages.NEEDSPACE.value,
    BuiltinPackages.AFTERPAGE.value,
    BuiltinPackages.PLACEINS.value,
    Package(name="scrlayer-scrpage", options="singlespacing=true"),
    Package(name="glossaries", options="acronym, savenumberlist=true"),
    BuiltinPackages.RAGGED2E.value,
    BuiltinPackages.LMODERN.value,
    BuiltinPackages.CLEVEREF.value,
    BuiltinPackages.CSQUOTES.value,
    BuiltinPackages.DRAFTWATERMARK.value,
    BuiltinPackages.FP.value,
    BuiltinPackages.TIKZPAGENODES.value,
    BuiltinPackages.HYPHENAT.value,
}


def imports_block() -> TeX:
    """Fallback font commands. Packages live in :data:`IMPORTS_PACKAGES`."""
    return Block(
        ProvideCommand("blenderfont", "\\sffamily"),
        ProvideCommand("dinfont", "\\rmfamily"),
    )


_HYPERSETUP_OPTIONS: list[str] = [
    "pdfpagemode={UseOutlines}",
    "bookmarksopen=true",
    "bookmarksopenlevel=0",
    "hypertexnames=false",
    "colorlinks=true",
    "citecolor=[rgb]{0.286, 0.427, 0.537}",
    "linkcolor=[rgb]{0.161, 0.31, 0.427}",
    "urlcolor=[rgb]{0.071, 0.212, 0.322}",
    "pdfstartview={FitV}",
    "unicode",
    "breaklinks=true",
]


def hyperref_block() -> TeX:
    """``\\hypersetup{...}``."""
    return Hypersetup(",".join(_HYPERSETUP_OPTIONS))


def sections_block() -> TeX:
    """KOMA section styles, counter wiring and chapter-mark indirection."""
    return Block(
        SetKomaFont("disposition", "\\blenderfont\\bfseries"),
        SetKomaFont("chapter", "\\LARGE\\blenderfont\\bfseries"),
        SetKomaFont("section", "\\Large\\blenderfont\\bfseries"),
        SetKomaFont("subsection", "\\large\\blenderfont\\bfseries"),
        SetKomaFont("subsubsection", "\\large\\blenderfont\\bfseries"),
        IncludeTeX(_TEX_DIR / "sections_marks.tex"),
        RedeclareSectionCommand(
            "chapter",
            "beforeskip=3ex plus 1ex minus 0.5ex,afterskip=1.5ex plus 0.3ex,style=section",
        ),
        RedeclareSectionCommand(
            "section",
            "beforeskip=4.5ex plus 1.5ex minus 0.5ex,afterskip=1.5ex plus 0.3ex",
        ),
        RedeclareSectionCommand(
            "subsection",
            "beforeskip=3.5ex plus 1ex minus 0.5ex,afterskip=1ex plus 0.2ex",
        ),
        RedeclareSectionCommand(
            "subsubsection",
            "beforeskip=2ex plus 0.5ex minus 0.3ex,afterskip=0.8ex plus 0.1ex",
        ),
        SetLength("parskip", "0.8ex plus 0.2ex minus 0.1ex"),
        NewCommand("decoRule", "\\rule{.8\\textwidth}{.4pt}"),
        CounterWithin("figure", "chapter"),
        CounterWithin("table", "chapter"),
        CounterWithout("equation", "chapter"),
        RenewCommand("thefigure", "\\thechapter.\\arabic{figure}"),
        RenewCommand("thetable", "\\thechapter.\\arabic{table}"),
    )


def typography_block() -> TeX:
    """Baseline stretch + lstset overlay + ``tex/typography.tex`` body."""
    return Block(
        RenewCommand("baselinestretch", "1.5"),
        SetLength("parskip", "0.5em plus 0.2em minus 0.1em"),
        SetLength("parindent", "0pt"),
        LstSet(
            {
                "float": "H",
                "belowskip": "-0.5em plus 0.2em",
                "aboveskip": "0.5em plus 0.2em",
                "keepspaces": True,
                "breaklines": True,
            }
        ),
        IncludeTeX(_TEX_DIR / "typography.tex"),
        RenewCommand("floatpagefraction", "0.8"),
        RenewCommand("topfraction", "0.9"),
        RenewCommand("bottomfraction", "0.9"),
        RenewCommand("textfraction", "0.1"),
        SetCounter("topnumber", 2),
        SetCounter("bottomnumber", 2),
        SetCounter("totalnumber", 4),
    )


def pagebreaks_block() -> TeX:
    """Page-break penalty/hook configuration."""
    return Block(
        NewLength("sectionminspace"),
        NewLength("subsectionminspace"),
        NewLength("subsubsectionminspace"),
        SetLength("sectionminspace", "12\\baselineskip"),
        SetLength("subsectionminspace", "10\\baselineskip"),
        SetLength("subsubsectionminspace", "8\\baselineskip"),
        NewCommand(
            "keeptogether",
            "\\begin{minipage}{\\linewidth}#1\\end{minipage}",
            n_args=1,
        ),
        NewCommand("protectparagraph", "\\nopagebreak[4]\\interlinepenalty=10000"),
        NewCommand(
            "conditionalpagebreak",
            "\\needspace{#1}",
            n_args=1,
            default="10\\baselineskip",
        ),
        IncludeTeX(_TEX_DIR / "pagebreaks.tex"),
    )


def toc_config_block() -> TeX:
    """Table-of-contents tweaks (uses ``\\@dottedtocline``)."""
    return IncludeTeX(_TEX_DIR / "toc_config.tex")


#: ``(type, singular, plural)`` rows for ``\\crefname`` / ``\\Crefname``.
_CREFNAMES: list[tuple[str, str, str]] = [
    ("figure", "Abbildung", "Abbildungen"),
    ("table", "Tabelle", "Tabellen"),
    ("equation", "Gleichung", "Gleichungen"),
    ("chapter", "Kapitel", "Kapitel"),
    ("section", "Abschnitt", "Abschnitte"),
    ("subsection", "Unterabschnitt", "Unterabschnitte"),
    ("subsubsection", "Unterunterabschnitt", "Unterunterabschnitte"),
    ("listing", "Listing", "Codeblock"),
    ("appendix", "Anhang", "Anhänge"),
    ("footnote", "Fußnote", "Fußnoten"),
    ("enumi", "Punkt", "Punkte"),
    ("page", "Seite", "Seiten"),
]


def cleveref_block() -> TeX:
    """German ``\\crefname`` / ``\\Crefname`` declarations."""
    parts: list[TeX] = []
    for ty, sg, pl in _CREFNAMES:
        parts.append(Crefname(ty, sg, pl, cap=False))
        parts.append(Crefname(ty, sg, pl, cap=True))
    return Block(*parts)


def glossary_settings_block() -> TeX:
    """Glossary style + entry-name overrides."""
    return Block(
        Command("makeglossaries"),
        IncludeTeX(_TEX_DIR / "glossary_style.tex"),
        Command("setglossarystyle", "manualfixedwidth"),
        RenewCommand("entryname", "Wort/Abkürzung"),
        RenewCommand("descriptionname", "Bedeutung"),
        RenewCommand("pagelistname", "Seite(n)"),
        Command("glsenablehyper"),
        RenewCommand("glsclearpage", ""),
        RenewCommand("acronymname", "Abkürzungsverzeichnis"),
        NewCommand("acr", "\\acrshort"),
    )


def page_setup_block() -> TeX:
    """Header / footer fields (`\\ohead`, `\\ifoot`, ...). Uses @-letter."""
    return Block(
        ClearPairOfPageStyles(),
        SetKomaFont("pageheadfoot", "\\color{gray}\\blenderfont"),
        SetKomaFont("pagenumber", "\\color{gray}\\blenderfont"),
        SetLength("footskip", "35pt"),
        IncludeTeX(_TEX_DIR / "page_setup.tex"),
        Pagestyle("scrheadings"),
    )


def path_defs_block(assets_path: str, variant: str) -> TeX:
    """Define ``\\classPath`` / ``\\fontsPath`` / ``\\imagesPath`` etc."""
    return Block(
        NewCommand("classPath", assets_path),
        NewCommand("fontsPath", "\\classPath/Fonts"),
        NewCommand("imagesPath", "\\classPath/Images"),
        ProvideCommand("ReportVariant", variant),
    )


def at_begin_document_block(toc: bool) -> TeX:
    """``\\AtBeginDocument`` body: frontmatter -> title -> (toc) -> mainmatter."""
    parts: list[TeX] = [
        FrontMatter,
        Command("maketitle"),
        # \def\istitlepage=\false\setstretch{1.0} is the original .cls trick: the
        # parameter-text absorbs \setstretch and the body is {1.0}. Preserved
        # verbatim as a Raw line — it relies on \def syntax no other primitive
        # gives us.
        Raw(
            "\\newpage\\def\\istitlepage=\\false\\setstretch{1.0}",
            escape_spaces=False,
            safe=False,
        ),
    ]
    if toc:
        parts.append(Command("tableofcontents"))
    parts.append(MainMatter)
    return AtBeginDocument(Block(*parts))


def at_end_document_block(
    has_glossary: bool, has_acronyms: bool, has_bibliography: bool
) -> TeX:
    """``\\AtEndDocument`` body: appendix + backmatter + glossaries + bib."""
    parts: list[TeX] = [
        Command("clearpage"),
        Appendix,
        KomaOptions("open=any"),
        BackMatter,
        Raw("\\cfoot*{}\\ohead*{}", escape_spaces=False, safe=False),
        Raw("\\noindent\\blenderfont", escape_spaces=False, safe=False),
    ]
    if has_glossary or has_acronyms:
        parts.append(Command("glsaddallunused"))
    if has_glossary:
        parts.append(RenewCommand("entryname", "Wort"))
        parts.append(Command("printglossary"))
    if has_acronyms:
        parts.append(RenewCommand("entryname", "Abkürzung"))
        opts = "type=\\acronymtype,title=Abkürzungen"
        parts.append(Command("printglossary", options=opts))
    if has_bibliography:
        parts.append(Command("makebib"))
    return AtEndDocument(Block(*parts))


# Re-export so downstream tests/users can introspect.
__all__ = [
    "IMPORTS_PACKAGES",
    "imports_block",
    "hyperref_block",
    "sections_block",
    "typography_block",
    "pagebreaks_block",
    "toc_config_block",
    "cleveref_block",
    "glossary_settings_block",
    "page_setup_block",
    "path_defs_block",
    "at_begin_document_block",
    "at_end_document_block",
]
