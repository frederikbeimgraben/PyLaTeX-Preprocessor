"""Example `.tex.py` file that builds a document with t-string templates.

    pytex examples/templatestring.tex.py --build

This example needs Python 3.14 or later for PEP 750 template strings. A
prebuilt `pytex` binary also works, because that binary always contains
Python 3.14.

`tex(t"...")` keeps the static text as literal LaTeX. It splices a TeX node
into the node tree without a change. It does the same for a list and for a
nested template. It escapes every other interpolated value for LaTeX.
"""

from pytex import tex
from pytex.commands.builtin import Bold, Emph, Enumerate, MakeTitle, Section, Title
from pytex.model.document import Document
from pytex.model.math import Frac, InlineMath

author = "Q. Walz & R&D (50% time)"  # `tex()` escapes `&` and `%` for LaTeX
points = [Bold("native nodes"), Emph("nested templates"), "plain text"]

__pytex__ = Document(
    preamble=Title("t-String Example"),
    body=tex(t"""{MakeTitle()}
{Section('Escaping')}
Interpolated text is escaped automatically — by {author}.

{Section('Nodes and math')}
Factories splice as-is: {Bold('bold')}, {Emph('emphasised')}, and the
quadratic term {InlineMath(Frac('-b', '2a'))}.

{Section('Lists')}
A list interpolates element by element:
{Enumerate(*points)}
"""),
)
