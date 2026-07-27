"""Example `.tex.py` file that builds a full document with the Python API.

    pytex examples/document.tex.py             # -> build/document.out.tex
    pytex examples/document.tex.py --build     # -> build/document.out.pdf

A `.tex.py` file is plain Python. It must define the `__pytex__` node at
module level. Here that node is a `Document`. PyTeX renders that node into
the rendered `.tex` file.
"""

from pytex.commands.builtin import (
    Bold,
    Emph,
    Enumerate,
    MakeTitle,
    Section,
    Title,
)
from pytex.model.concat import Concat
from pytex.model.document import Document
from pytex.model.math import DisplayMath, Frac

__pytex__ = Document(
    preamble=Title("PyTeX Example"),
    body=Concat(
        MakeTitle(),
        Section("Text"),
        "A paragraph with ",
        Bold("bold"),
        " and ",
        Emph("emphasised"),
        " words.",
        Section("Math"),
        "An equation built in Python:",
        DisplayMath(Concat("x = ", Frac("-b", "2a"))),
        Section("Lists"),
        Enumerate("first", "second", "third"),
    ),
)
