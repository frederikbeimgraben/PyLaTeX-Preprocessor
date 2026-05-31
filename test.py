from pytex.commands.builtin import (
    Author,
    Bigskip,
    Bold,
    Center,
    Cite,
    Date,
    Emph,
    Enumerate,
    Footnote,
    Hfill,
    Itemize,
    Label,
    Large,
    MakeTitle,
    Newline,
    Newpage,
    Paragraph,
    Ref,
    Section,
    Subsection,
    Subsubsection,
    TableOfContents,
    Texttt,
    Title,
)
from pytex.model.concat import Concat
from pytex.model.document import Document
from pytex.model.environment import Environment
from pytex.model.math import (
    Align,
    Bmatrix,
    Cases,
    DisplayMath,
    Eqref,
    Equation,
    Frac,
    Int,
    Math,
    Mathbb,
    Pmatrix,
    Sqrt,
    Sub,
    Sum,
    Super,
    Text,
)
from pytex.model.raw import Raw

preamble = Concat(
    Title("PyTeX Showcase"),
    Author("Frederik Beimgraben"),
    Date(r"\today"),
)

intro = Concat(
    Section("Introduction", short="Intro"),
    Label("sec:intro"),
    "Welcome to ",
    Bold("PyTeX"),
    ", a ",
    Emph("type-safe"),
    " LaTeX generation library written in ",
    Texttt("Python"),
    ". See ",
    Ref("sec:math"),
    " for math examples.",
    Newline(),
    Footnote("Footnotes work too."),
)

lists = Concat(
    Subsection("Lists"),
    "Unordered:",
    Itemize("apples", "oranges", "kiwis"),
    "Ordered:",
    Enumerate("first", "second", "third"),
)

math_section = Concat(
    Section("Math"),
    Label("sec:math"),
    "Inline math: ",
    Math(Concat(Frac("a", "b"), " + ", Sqrt("x", n="3"))),
    ".",
    Newline(),
    "Display math:",
    DisplayMath(Concat(Sum("i=1", "n"), " i = ", Frac("n(n+1)", "2"))),
    Subsubsection("Equation"),
    Equation(
        Concat(
            "E = mc",
            Super("", "2"),
            Label("eq:emc"),
        )
    ),
    "See ", Eqref("eq:emc"), ".",
    Subsubsection("Align"),
    Align(
        Concat(
            "f(x) &= x", Super("", "2"), Raw(" + 2x + 1 \\\\"),
            "g(x) &= ", Sqrt("x"), Raw(" + 1"),
        )
    ),
    Subsubsection("Cases"),
    DisplayMath(
        Concat(
            "|x| = ",
            Cases(
                Raw(r"x, & x \geq 0 \\ -x, & x < 0"),
            ),
        )
    ),
    Subsubsection("Matrices"),
    DisplayMath(
        Concat(
            "A = ",
            Pmatrix([["1", "2"], ["3", "4"]]),
            ", \\quad B = ",
            Bmatrix([["a", "b", "c"], ["d", "e", "f"]]),
        )
    ),
    Subsubsection(r"Integrals \& sets"),
    DisplayMath(
        Concat(
            Int("0", r"\infty"),
            " e",
            Super("", "-x"),
            r" \, dx = 1, \quad x \in ",
            Mathbb("R"),
        )
    ),
    Subsubsection("Subscripts"),
    Math(Concat(Sub("x", "i,j"), " + ", Sub("y", "k"))),
    Newline(),
    "Mixed: ",
    Math(Concat(Text("for all "), "x ", Raw(r"\in "), Mathbb("N"))),
    ".",
)

formatting = Concat(
    Section("Formatting"),
    Large("Large text. "),
    "Normal. ",
    Bold(Italicized := Emph("bold-emph")),
    Hfill(),
    " right-flushed",
    Newline(),
    Bigskip(),
    Paragraph("A paragraph heading."),
    "Body of paragraph.",
)

refs = Concat(
    Section("References"),
    "See ", Cite("knuth1984", "lamport1994"), " for background.",
)

body = Concat(
    MakeTitle(),
    TableOfContents(),
    Newpage(),
    intro,
    lists,
    math_section,
    formatting,
    refs,
    Environment("abstract", "Custom environment test."),
    Center("Centered closing line."),
)

doc = Document(
    body,
    document_class="article",
    document_class_options={"a4paper", "11pt", ("fontsize", "12pt")},
    preamble=preamble,
)

print(doc)
