from ..interface.tex import TeX
from ..model.concat import Concat
from ..model.control_sequence import ControlSequence, Parameter
from ..model.environment import Environment
from ..model.raw import Raw


def _section_like(name: str, title: TeX | str, short: TeX | str | None) -> TeX:
    if short is None:
        return ControlSequence(name, (Parameter(title),))
    return ControlSequence(name, (Parameter(short, optional=True), Parameter(title)))


def Part(title: TeX | str, short: TeX | str | None = None) -> TeX:
    return _section_like("part", title, short)


def Chapter(title: TeX | str, short: TeX | str | None = None) -> TeX:
    return _section_like("chapter", title, short)


def Section(title: TeX | str, short: TeX | str | None = None) -> TeX:
    return _section_like("section", title, short)


def Subsection(title: TeX | str, short: TeX | str | None = None) -> TeX:
    return _section_like("subsection", title, short)


def Subsubsection(title: TeX | str, short: TeX | str | None = None) -> TeX:
    return _section_like("subsubsection", title, short)


def Paragraph(title: TeX | str) -> TeX:
    return ControlSequence("paragraph", (Parameter(title),))


def Subparagraph(title: TeX | str) -> TeX:
    return ControlSequence("subparagraph", (Parameter(title),))


def Textbf(body: TeX | str) -> TeX:
    return ControlSequence("textbf", (Parameter(body),))


def Textit(body: TeX | str) -> TeX:
    return ControlSequence("textit", (Parameter(body),))


def Textsl(body: TeX | str) -> TeX:
    return ControlSequence("textsl", (Parameter(body),))


def Textsc(body: TeX | str) -> TeX:
    return ControlSequence("textsc", (Parameter(body),))


def Texttt(body: TeX | str) -> TeX:
    return ControlSequence("texttt", (Parameter(body),))


def Textsf(body: TeX | str) -> TeX:
    return ControlSequence("textsf", (Parameter(body),))


def Textrm(body: TeX | str) -> TeX:
    return ControlSequence("textrm", (Parameter(body),))


def Textmd(body: TeX | str) -> TeX:
    return ControlSequence("textmd", (Parameter(body),))


def Textup(body: TeX | str) -> TeX:
    return ControlSequence("textup", (Parameter(body),))


def Emph(body: TeX | str) -> TeX:
    return ControlSequence("emph", (Parameter(body),))


def Underline(body: TeX | str) -> TeX:
    return ControlSequence("underline", (Parameter(body),))


def Bold(body: TeX | str) -> TeX:
    return Textbf(body)


def Italic(body: TeX | str) -> TeX:
    return Textit(body)


def Newline() -> TeX:
    return Raw("\\\\")


def Linebreak(n: int | None = None) -> TeX:
    if n is None:
        return ControlSequence("linebreak", ())
    return ControlSequence("linebreak", (Parameter(str(n), optional=True),))


def Newpage() -> TeX:
    return ControlSequence("newpage", ())


def Clearpage() -> TeX:
    return ControlSequence("clearpage", ())


def Cleardoublepage() -> TeX:
    return ControlSequence("cleardoublepage", ())


def Pagebreak(n: int | None = None) -> TeX:
    if n is None:
        return ControlSequence("pagebreak", ())
    return ControlSequence("pagebreak", (Parameter(str(n), optional=True),))


def Hspace(amount: str, star: bool = False) -> TeX:
    name = "hspace*" if star else "hspace"
    return ControlSequence(name, (Parameter(amount),))


def Vspace(amount: str, star: bool = False) -> TeX:
    name = "vspace*" if star else "vspace"
    return ControlSequence(name, (Parameter(amount),))


def Hfill() -> TeX:
    return ControlSequence("hfill", ())


def Vfill() -> TeX:
    return ControlSequence("vfill", ())


def Smallskip() -> TeX:
    return ControlSequence("smallskip", ())


def Medskip() -> TeX:
    return ControlSequence("medskip", ())


def Bigskip() -> TeX:
    return ControlSequence("bigskip", ())


def Noindent() -> TeX:
    return ControlSequence("noindent", ())


def Indent() -> TeX:
    return ControlSequence("indent", ())


def Item(body: TeX | str | None = None, label: TeX | str | None = None) -> TeX:
    head: TeX = (
        ControlSequence("item", (Parameter(label, optional=True),))
        if label is not None
        else ControlSequence("item", ())
    )
    if body is None:
        return head
    return Concat(head, Raw(" "), body)


def Itemize(*items: TeX | str) -> TeX:
    return Environment(
        "itemize",
        Concat(*(it if _is_item(it) else Item(it) for it in items)),
    )


def Enumerate(*items: TeX | str) -> TeX:
    return Environment(
        "enumerate",
        Concat(*(it if _is_item(it) else Item(it) for it in items)),
    )


def Description(*items: tuple[TeX | str, TeX | str] | TeX) -> TeX:
    body_parts: list[TeX] = []
    for it in items:
        if isinstance(it, tuple):
            term, desc = it
            body_parts.append(Item(desc, label=term))
        else:
            body_parts.append(it)
    return Environment("description", Concat(*body_parts))


def _is_item(node: TeX | str) -> bool:
    if isinstance(node, Concat):
        first = node.elements[0] if node.elements else None
        return isinstance(first, ControlSequence) and first.name == "item"
    return isinstance(node, ControlSequence) and node.name == "item"


def Label(name: str) -> TeX:
    return ControlSequence("label", (Parameter(name),))


def Ref(name: str) -> TeX:
    return ControlSequence("ref", (Parameter(name),))


def Pageref(name: str) -> TeX:
    return ControlSequence("pageref", (Parameter(name),))


def Nameref(name: str) -> TeX:
    return ControlSequence("nameref", (Parameter(name),))


def Cite(*keys: str, prenote: str | None = None) -> TeX:
    key_param = Parameter(",".join(keys))
    if prenote is None:
        return ControlSequence("cite", (key_param,))
    return ControlSequence("cite", (Parameter(prenote, optional=True), key_param))


def Title(title: TeX | str) -> TeX:
    return ControlSequence("title", (Parameter(title),))


def Author(author: TeX | str) -> TeX:
    return ControlSequence("author", (Parameter(author),))


def Date(date: TeX | str) -> TeX:
    return ControlSequence("date", (Parameter(date),))


def Today() -> TeX:
    return ControlSequence("today", ())


def MakeTitle() -> TeX:
    return ControlSequence("maketitle", ())


def Thanks(body: TeX | str) -> TeX:
    return ControlSequence("thanks", (Parameter(body),))


def TableOfContents() -> TeX:
    return ControlSequence("tableofcontents", ())


def ListOfFigures() -> TeX:
    return ControlSequence("listoffigures", ())


def ListOfTables() -> TeX:
    return ControlSequence("listoftables", ())


def Footnote(body: TeX | str) -> TeX:
    return ControlSequence("footnote", (Parameter(body),))


def Footnotemark(n: int | None = None) -> TeX:
    if n is None:
        return ControlSequence("footnotemark", ())
    return ControlSequence("footnotemark", (Parameter(str(n), optional=True),))


def Footnotetext(body: TeX | str) -> TeX:
    return ControlSequence("footnotetext", (Parameter(body),))


def Input(path: str) -> TeX:
    return ControlSequence("input", (Parameter(path),))


def Include(path: str) -> TeX:
    return ControlSequence("include", (Parameter(path),))


def IncludeOnly(*paths: str) -> TeX:
    return ControlSequence("includeonly", (Parameter(",".join(paths)),))


def Center(body: TeX | str) -> TeX:
    return Environment("center", body)


def FlushLeft(body: TeX | str) -> TeX:
    return Environment("flushleft", body)


def FlushRight(body: TeX | str) -> TeX:
    return Environment("flushright", body)


def Centering() -> TeX:
    return ControlSequence("centering", ())


def Raggedright() -> TeX:
    return ControlSequence("raggedright", ())


def Raggedleft() -> TeX:
    return ControlSequence("raggedleft", ())


def Quote(body: TeX | str) -> TeX:
    return Environment("quote", body)


def Quotation(body: TeX | str) -> TeX:
    return Environment("quotation", body)


def Verse(body: TeX | str) -> TeX:
    return Environment("verse", body)


def Verbatim(body: TeX | str) -> TeX:
    return Environment("verbatim", body)


def Verb(body: str, delim: str = "|") -> TeX:
    return Raw(f"\\verb{delim}{body}{delim}")


def Tiny(body: TeX | str) -> TeX:
    return Concat(ControlSequence("tiny", ()), Raw(" "), body)


def Scriptsize(body: TeX | str) -> TeX:
    return Concat(ControlSequence("scriptsize", ()), Raw(" "), body)


def Footnotesize(body: TeX | str) -> TeX:
    return Concat(ControlSequence("footnotesize", ()), Raw(" "), body)


def Small(body: TeX | str) -> TeX:
    return Concat(ControlSequence("small", ()), Raw(" "), body)


def Normalsize(body: TeX | str) -> TeX:
    return Concat(ControlSequence("normalsize", ()), Raw(" "), body)


def Large(body: TeX | str) -> TeX:
    return Concat(ControlSequence("large", ()), Raw(" "), body)


def LLarge(body: TeX | str) -> TeX:
    return Concat(ControlSequence("Large", ()), Raw(" "), body)


def LLLarge(body: TeX | str) -> TeX:
    return Concat(ControlSequence("LARGE", ()), Raw(" "), body)


def Huge(body: TeX | str) -> TeX:
    return Concat(ControlSequence("huge", ()), Raw(" "), body)


def HHuge(body: TeX | str) -> TeX:
    return Concat(ControlSequence("Huge", ()), Raw(" "), body)


def Group(body: TeX | str) -> TeX:
    return Concat(Raw("{"), body, Raw("}"))
