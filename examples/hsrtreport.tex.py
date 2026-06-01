"""`.tex.py` example: a Reutlingen University (HSRT) report.

    pytex examples/hsrtreport.tex.py --build   # -> build/hsrtreport.out.pdf

`HSRTReport` is a `scrbook` document that wires up the full HSRT preamble
(brand colours, hyperref, cleveref names, listing styles, glossaries) from a
few flags. Here it shows chapters/sections plus the HSRT callout boxes.

Note: the HSRT class always loads `biblatex`, so compiling needs `biber`
installed (tectonic runs it automatically). A real report would usually also
add a `TitlePage(...)` at the top of the body; it is omitted here because it
selects the Blender/DIN brand fonts, which must be installed locally.
"""

from pytex.commands.builtin import Chapter, Enumerate, Section
from pytex.model.concat import Concat
from pytex.model.math import DisplayMath, Frac
from pytex_hsrtreport import (
    HSRTReport,
    ImportantBox,
    InfoBox,
    SuccessBox,
    Variant,
    WarningBox,
)
from pytex_hsrtreport.titlepage import TitlePageDataLine

__pytex__ = HSRTReport(
    title_page=True,
    variant=Variant.INF,
    show_toc=True,
    title="HSRT Report Example",
    author="PyTeX",
    abstract="Lorem ipsum dolor sit amet",
    keywords="Example, TeX",
    data_lines=(TitlePageDataLine("Test", "Test"),),
    show_footer_logos=True,
    body=Concat(
        Chapter("Introduction"),
        "This document is generated with ",
        "the HSRT report class via PyTeX.",
        Section("Callout boxes"),
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
        Section("Math and lists"),
        "Inline content works as usual:",
        DisplayMath(Concat("x = ", Frac("-b", "2a"))),
        Enumerate("first point", "second point", "third point"),
    ),
)
