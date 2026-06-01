"""`.tex.py` example: build a full document with the Python API.

    pytex examples/document.tex.py            # -> document.out.tex
    pytex examples/document.tex.py --build     # -> build/document.out.pdf

A `.tex.py` file is plain Python that exposes a module-level ``__pytex__``
holding a ``TeX`` node (here a ``Document``). The builder renders it.
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
