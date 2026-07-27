"""Golden sample node tree that the Python API builds directly.

This sample uses a wide spread of `TeX` node types. It has sectioning, inline
markup, lists, descriptions, footnotes, cross-references, inline math and
display math. The golden file freezes the rendered `.tex` file, so a silent
change of the render output fails the test.

This file uses no Python 3.14 t-string syntax, so it imports under the Python
3.13 test interpreter. The module-level `__pytex__` node holds the node tree.
"""

from pytex.commands.builtin import (
    Bold,
    Description,
    Emph,
    Enumerate,
    Footnote,
    Itemize,
    Label,
    MakeTitle,
    Ref,
    Section,
    Subsection,
    Title,
)
from pytex.model.concat import Concat
from pytex.model.document import Document
from pytex.model.math import DisplayMath, Frac, InlineMath

__pytex__ = Document(
    preamble=Title("PyTeX Node-Tree Sample"),
    body=Concat(
        MakeTitle(),
        Section("Text"),
        Label("sec:text"),
        "A paragraph with ",
        Bold("bold"),
        ", ",
        Emph("emphasised"),
        " words and a footnote",
        Footnote("a footnote body"),
        ".",
        Subsection("Lists"),
        Itemize("alpha", "beta", "gamma"),
        Enumerate("first", "second", "third"),
        Description(("Term", "definition of the term")),
        Section("Math"),
        "Inline ",
        InlineMath(Concat("a = ", Frac("1", "2"))),
        " and display:",
        DisplayMath(Concat("x = ", Frac("-b", "2a"))),
        Section("Cross-reference"),
        "See section ",
        Ref("sec:text"),
        ".",
    ),
)
