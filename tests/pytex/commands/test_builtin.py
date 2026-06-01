from pytex.commands.builtin import (
    Author,
    Bold,
    Center,
    Cite,
    Date,
    Description,
    Emph,
    Enumerate,
    Footnote,
    Hfill,
    Indent,
    Italic,
    Item,
    Itemize,
    Label,
    MakeTitle,
    Newline,
    Newpage,
    Pageref,
    Paragraph,
    Quote,
    Ref,
    Section,
    Subsection,
    Subsubsection,
    TableOfContents,
    Textbf,
    Texttt,
    Title,
    Today,
)
from pytex.model.control_sequence import ControlSequence


def test_section_basic():
    assert Section("Intro").rendered == r"\section{Intro}"


def test_section_with_short():
    assert Section("Long", "Short").rendered == r"\section[Short]{Long}"


def test_subsection():
    assert Subsection("x").rendered == r"\subsection{x}"


def test_subsubsection():
    assert Subsubsection("x").rendered == r"\subsubsection{x}"


def test_paragraph():
    assert Paragraph("h").rendered == r"\paragraph{h}"


def test_textbf():
    assert Textbf("x").rendered == r"\textbf{x}"


def test_emph():
    assert Emph("x").rendered == r"\emph{x}"


def test_texttt():
    assert Texttt("x").rendered == r"\texttt{x}"


def test_bold_aliases_textbf():
    assert Bold("x").rendered == Textbf("x").rendered


def test_italic_aliases_textit():
    assert Italic("x").rendered == r"\textit{x}"


def test_newline_renders_double_backslash():
    assert Newline().rendered == r"\\"


def test_newpage():
    assert Newpage().rendered == r"\newpage"


def test_hfill():
    assert Hfill().rendered == r"\hfill"


def test_indent():
    assert Indent().rendered == r"\indent"


def test_item_no_body():
    out = Item().rendered
    assert out == r"\item"


def test_item_with_body():
    out = Item("hi").rendered
    assert r"\item" in out and "hi" in out


def test_item_with_label():
    out = Item("body", label="lbl").rendered
    assert r"\item[lbl]" in out and "body" in out


def test_itemize():
    out = Itemize("a", "b").rendered
    assert out.startswith(r"\begin{itemize}")
    assert out.endswith(r"\end{itemize}")
    assert r"\item a" in out and r"\item b" in out


def test_enumerate():
    out = Enumerate("a", "b").rendered
    assert out.startswith(r"\begin{enumerate}")


def test_description():
    out = Description(("term1", "desc1"), ("term2", "desc2")).rendered
    assert r"\item[term1] desc1" in out
    assert r"\item[term2] desc2" in out


def test_label_ref_pageref():
    assert Label("x").rendered == r"\label{x}"
    assert Ref("x").rendered == r"\ref{x}"
    assert Pageref("x").rendered == r"\pageref{x}"


def test_cite_single():
    assert Cite("knuth").rendered == r"\cite{knuth}"


def test_cite_multiple():
    assert Cite("a", "b").rendered == r"\cite{a,b}"


def test_cite_with_prenote():
    out = Cite("k", prenote="see").rendered
    assert out == r"\cite[see]{k}"


def test_title_author_date():
    assert Title("T").rendered == r"\title{T}"
    assert Author("A").rendered == r"\author{A}"
    assert Date("D").rendered == r"\date{D}"


def test_today():
    assert Today().rendered == r"\today"


def test_maketitle():
    assert MakeTitle().rendered == r"\maketitle"


def test_table_of_contents():
    assert TableOfContents().rendered == r"\tableofcontents"


def test_footnote():
    assert Footnote("note").rendered == r"\footnote{note}"


def test_center_env():
    out = Center("x").rendered
    assert out == r"\begin{center}x\end{center}"


def test_quote_env():
    assert Quote("x").rendered == r"\begin{quote}x\end{quote}"


def test_section_returns_control_sequence():
    assert isinstance(Section("x"), ControlSequence)
