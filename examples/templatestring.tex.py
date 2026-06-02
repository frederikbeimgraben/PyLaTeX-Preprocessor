"""`.tex.py` example: build a document with t-string templates (Python 3.14+).

    pytex examples/templatestring.tex.py --build

Requires Python 3.14 (PEP 750 template strings) — or a prebuilt pytex binary,
which is 3.14 regardless of the host. ``tex(t"...")`` keeps the static text as
literal LaTeX, LaTeX-escapes interpolated values, and splices ``TeX`` nodes
as-is (lists and nested templates too).
"""

from pytex import tex
from pytex.commands.builtin import Bold, Emph, Enumerate, MakeTitle, Section, Title
from pytex.model.document import Document
from pytex.model.math import Frac, InlineMath

author = "Q. Walz & R&D (50% time)"  # specials get escaped when interpolated
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
