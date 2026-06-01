from ..interface.tex import TeX
from ..model.concat import Concat
from ..model.control_sequence import ControlSequence, Parameter
from ..model.environment import Environment
from ..model.raw import Raw
from ..registry import Registry

__all__ = [
    "Author",
    "BeginAccSupp",
    "Bigskip",
    "Blenderfont",
    "Bold",
    "Center",
    "Centering",
    "Chapter",
    "ChapterStar",
    "Cite",
    "Cleardoublepage",
    "Clearpage",
    "Date",
    "Description",
    "Dinfont",
    "Emph",
    "EndAccSupp",
    "Enumerate",
    "FlushLeft",
    "FlushRight",
    "Footnote",
    "Footnotemark",
    "Footnotetext",
    "Foreach",
    "Group",
    "Hfill",
    "Hspace",
    "Immediate",
    "Include",
    "IncludeOnly",
    "Indent",
    "Input",
    "Inputfile",
    "Italic",
    "Item",
    "Itemize",
    "Label",
    "Linebreak",
    "ListOfFigures",
    "ListOfTables",
    "MakeTitle",
    "Medskip",
    "Nameref",
    "Newglossarystyle",
    "Newline",
    "Newpage",
    "Noindent",
    "Pagebreak",
    "Pagenumbering",
    "Pageref",
    "Paragraph",
    "Part",
    "PartStar",
    "Quotation",
    "Quote",
    "Raggedleft",
    "Raggedright",
    "Ref",
    "Rule",
    "Section",
    "SectionStar",
    "Smallskip",
    "Subparagraph",
    "Subsection",
    "SubsectionStar",
    "Subsubsection",
    "SubsubsectionStar",
    "TableOfContents",
    "Textbf",
    "Textit",
    "Textmd",
    "Textrm",
    "Textsc",
    "Textsf",
    "Textsl",
    "Texttt",
    "Textup",
    "Thanks",
    "Title",
    "Today",
    "Underline",
    "Verb",
    "Verbatim",
    "Verbatiminput",
    "Verse",
    "Vfill",
    "Vspace",
    "Whiledo",
    "Write18",
]


def _section_like(name: str, title: TeX | str, short: TeX | str | None) -> TeX:
    if short is None:
        return ControlSequence(name, (Parameter(title),))
    return ControlSequence(name, (Parameter(short, optional=True), Parameter(title)))


@Registry.add
def Part(title: TeX | str, short: TeX | str | None = None) -> TeX:
    return _section_like("part", title, short)


@Registry.add
def Chapter(title: TeX | str, short: TeX | str | None = None) -> TeX:
    return _section_like("chapter", title, short)


@Registry.add
def Section(title: TeX | str, short: TeX | str | None = None) -> TeX:
    return _section_like("section", title, short)


@Registry.add
def Subsection(title: TeX | str, short: TeX | str | None = None) -> TeX:
    return _section_like("subsection", title, short)


@Registry.add
def Subsubsection(title: TeX | str, short: TeX | str | None = None) -> TeX:
    return _section_like("subsubsection", title, short)


@Registry.add
def Paragraph(title: TeX | str) -> TeX:
    return ControlSequence("paragraph", (Parameter(title),))


@Registry.add
def Subparagraph(title: TeX | str) -> TeX:
    return ControlSequence("subparagraph", (Parameter(title),))


@Registry.add
def PartStar(title: TeX | str) -> TeX:
    return ControlSequence("part*", (Parameter(title),))


@Registry.add
def ChapterStar(title: TeX | str) -> TeX:
    return ControlSequence("chapter*", (Parameter(title),))


@Registry.add
def SectionStar(title: TeX | str) -> TeX:
    return ControlSequence("section*", (Parameter(title),))


@Registry.add
def SubsectionStar(title: TeX | str) -> TeX:
    return ControlSequence("subsection*", (Parameter(title),))


@Registry.add
def SubsubsectionStar(title: TeX | str) -> TeX:
    return ControlSequence("subsubsection*", (Parameter(title),))


@Registry.add
def Textbf(body: TeX | str) -> TeX:
    return ControlSequence("textbf", (Parameter(body),))


@Registry.add
def Textit(body: TeX | str) -> TeX:
    return ControlSequence("textit", (Parameter(body),))


@Registry.add
def Textsl(body: TeX | str) -> TeX:
    return ControlSequence("textsl", (Parameter(body),))


@Registry.add
def Textsc(body: TeX | str) -> TeX:
    return ControlSequence("textsc", (Parameter(body),))


@Registry.add
def Texttt(body: TeX | str) -> TeX:
    return ControlSequence("texttt", (Parameter(body),))


@Registry.add
def Textsf(body: TeX | str) -> TeX:
    return ControlSequence("textsf", (Parameter(body),))


@Registry.add
def Textrm(body: TeX | str) -> TeX:
    return ControlSequence("textrm", (Parameter(body),))


@Registry.add
def Textmd(body: TeX | str) -> TeX:
    return ControlSequence("textmd", (Parameter(body),))


@Registry.add
def Textup(body: TeX | str) -> TeX:
    return ControlSequence("textup", (Parameter(body),))


@Registry.add
def Emph(body: TeX | str) -> TeX:
    return ControlSequence("emph", (Parameter(body),))


@Registry.add
def Underline(body: TeX | str) -> TeX:
    return ControlSequence("underline", (Parameter(body),))


@Registry.add
def Bold(body: TeX | str) -> TeX:
    return Textbf(body)


@Registry.add
def Italic(body: TeX | str) -> TeX:
    return Textit(body)


@Registry.add
def Newline() -> TeX:
    return Raw("\\\\")


@Registry.add
def Linebreak(n: int | None = None) -> TeX:
    if n is None:
        return ControlSequence("linebreak", ())
    return ControlSequence("linebreak", (Parameter(str(n), optional=True),))


@Registry.add
def Newpage() -> TeX:
    return ControlSequence("newpage", ())


@Registry.add
def Clearpage() -> TeX:
    return ControlSequence("clearpage", ())


@Registry.add
def Cleardoublepage() -> TeX:
    return ControlSequence("cleardoublepage", ())


@Registry.add
def Pagebreak(n: int | None = None) -> TeX:
    if n is None:
        return ControlSequence("pagebreak", ())
    return ControlSequence("pagebreak", (Parameter(str(n), optional=True),))


@Registry.add
def Hspace(amount: str, star: bool = False) -> TeX:
    name = "hspace*" if star else "hspace"
    return ControlSequence(name, (Parameter(amount),))


@Registry.add
def Vspace(amount: str, star: bool = False) -> TeX:
    name = "vspace*" if star else "vspace"
    return ControlSequence(name, (Parameter(amount),))


@Registry.add
def Hfill() -> TeX:
    return ControlSequence("hfill", ())


@Registry.add
def Vfill() -> TeX:
    return ControlSequence("vfill", ())


@Registry.add
def Smallskip() -> TeX:
    return ControlSequence("smallskip", ())


@Registry.add
def Medskip() -> TeX:
    return ControlSequence("medskip", ())


@Registry.add
def Bigskip() -> TeX:
    return ControlSequence("bigskip", ())


@Registry.add
def Noindent() -> TeX:
    return ControlSequence("noindent", ())


@Registry.add
def Indent() -> TeX:
    return ControlSequence("indent", ())


@Registry.add
def Item(body: TeX | str | None = None, label: TeX | str | None = None) -> TeX:
    head: TeX = (
        ControlSequence("item", (Parameter(label, optional=True),))
        if label is not None
        else ControlSequence("item", ())
    )
    if body is None:
        return head
    return Concat(head, Raw(" "), body)


@Registry.add
def Itemize(*items: TeX | str) -> TeX:
    return Environment(
        "itemize",
        Concat(*(it if _is_item(it) else Item(it) for it in items)),
    )


@Registry.add
def Enumerate(*items: TeX | str) -> TeX:
    return Environment(
        "enumerate",
        Concat(*(it if _is_item(it) else Item(it) for it in items)),
    )


def _describe_item(item: tuple[TeX | str, TeX | str] | TeX) -> TeX | str:
    """A `(term, description)` pair becomes a labelled `\\item`; nodes pass through."""
    if isinstance(item, tuple):
        term, desc = item
        return Item(desc, label=term)
    return item


@Registry.add
def Description(*items: tuple[TeX | str, TeX | str] | TeX) -> TeX:
    return Environment(
        "description",
        Concat(*(_describe_item(it) for it in items)),
    )


def _is_item(node: TeX | str) -> bool:
    return isinstance(node, ControlSequence) and node.name == "item"


@Registry.add
def Label(name: str) -> TeX:
    return ControlSequence("label", (Parameter(name),))


@Registry.add
def Ref(name: str) -> TeX:
    return ControlSequence("ref", (Parameter(name),))


@Registry.add
def Pageref(name: str) -> TeX:
    return ControlSequence("pageref", (Parameter(name),))


@Registry.add
def Nameref(name: str) -> TeX:
    return ControlSequence("nameref", (Parameter(name),))


@Registry.add
def Cite(*keys: str, prenote: str | None = None) -> TeX:
    key_param = Parameter(",".join(keys))
    if prenote is None:
        return ControlSequence("cite", (key_param,))
    return ControlSequence("cite", (Parameter(prenote, optional=True), key_param))


@Registry.add
def Title(title: TeX | str) -> TeX:
    return ControlSequence("title", (Parameter(title),))


@Registry.add
def Author(author: TeX | str) -> TeX:
    return ControlSequence("author", (Parameter(author),))


@Registry.add
def Date(date: TeX | str) -> TeX:
    return ControlSequence("date", (Parameter(date),))


@Registry.add
def Today() -> TeX:
    return ControlSequence("today", ())


@Registry.add
def MakeTitle() -> TeX:
    return ControlSequence("maketitle", ())


@Registry.add
def Thanks(body: TeX | str) -> TeX:
    return ControlSequence("thanks", (Parameter(body),))


@Registry.add
def TableOfContents() -> TeX:
    return ControlSequence("tableofcontents", ())


@Registry.add
def ListOfFigures() -> TeX:
    return ControlSequence("listoffigures", ())


@Registry.add
def ListOfTables() -> TeX:
    return ControlSequence("listoftables", ())


@Registry.add
def Footnote(body: TeX | str) -> TeX:
    return ControlSequence("footnote", (Parameter(body),))


@Registry.add
def Footnotemark(n: int | None = None) -> TeX:
    if n is None:
        return ControlSequence("footnotemark", ())
    return ControlSequence("footnotemark", (Parameter(str(n), optional=True),))


@Registry.add
def Footnotetext(body: TeX | str) -> TeX:
    return ControlSequence("footnotetext", (Parameter(body),))


@Registry.add
def Input(path: str) -> TeX:
    return ControlSequence("input", (Parameter(path),))


@Registry.add
def Include(path: str) -> TeX:
    return ControlSequence("include", (Parameter(path),))


@Registry.add
def IncludeOnly(*paths: str) -> TeX:
    return ControlSequence("includeonly", (Parameter(",".join(paths)),))


@Registry.add
def Center(body: TeX | str) -> TeX:
    return Environment("center", body)


@Registry.add
def FlushLeft(body: TeX | str) -> TeX:
    return Environment("flushleft", body)


@Registry.add
def FlushRight(body: TeX | str) -> TeX:
    return Environment("flushright", body)


@Registry.add
def Centering() -> TeX:
    return ControlSequence("centering", ())


@Registry.add
def Raggedright() -> TeX:
    return ControlSequence("raggedright", ())


@Registry.add
def Raggedleft() -> TeX:
    return ControlSequence("raggedleft", ())


@Registry.add
def Quote(body: TeX | str) -> TeX:
    return Environment("quote", body)


@Registry.add
def Quotation(body: TeX | str) -> TeX:
    return Environment("quotation", body)


@Registry.add
def Verse(body: TeX | str) -> TeX:
    return Environment("verse", body)


@Registry.add
def Verbatim(body: TeX | str) -> TeX:
    return Environment("verbatim", body)


@Registry.add
def Verb(body: str, delim: str = "|") -> TeX:
    return Raw(f"\\verb{delim}{body}{delim}")


# Size switches moved to pytex/commands/font.py (zero-arg ControlSequence wrappers).
# Compose with `Concat(Large(), " body")` for inline use.


@Registry.add
def Group(body: TeX | str) -> TeX:
    return Concat(Raw("{"), body, Raw("}"))


@Registry.add
def Rule(width: str, thickness: str) -> TeX:
    return ControlSequence("rule", (Parameter(width), Parameter(thickness)))


@Registry.add
def Pagenumbering(scheme: str) -> TeX:
    return ControlSequence("pagenumbering", (Parameter(scheme),))


@Registry.add
def Immediate(body: TeX | str) -> TeX:
    return Concat(ControlSequence("immediate", ()), Raw(" "), body)


@Registry.add
def Write18(text: str) -> TeX:
    return Raw("\\write18{" + text + "}")


@Registry.add
def Verbatiminput(path: str) -> TeX:
    return ControlSequence("verbatiminput", (Parameter(path),))


@Registry.add
def Inputfile(path: str) -> TeX:
    """Alias for `\\input{path}` — `Input` already defined above as Input(path)."""
    return ControlSequence("input", (Parameter(path),))


@Registry.add
def Whiledo(condition: TeX | str, body: TeX | str) -> TeX:
    return ControlSequence("whiledo", (Parameter(condition), Parameter(body)))


@Registry.add
def Foreach(var: str, values: str, body: TeX | str) -> TeX:
    return Concat(
        Raw(f"\\foreach {var} in {{{values}}}"),
        Raw("{"),
        body,
        Raw("}"),
    )


@Registry.add
def BeginAccSupp(options: dict[str, str]) -> TeX:
    return ControlSequence("BeginAccSupp", (Parameter(options),))


@Registry.add
def EndAccSupp() -> TeX:
    return ControlSequence("EndAccSupp", ())


@Registry.add
def Newglossarystyle(name: str, body: TeX | str) -> TeX:
    return ControlSequence("newglossarystyle", (Parameter(name), Parameter(body)))


@Registry.add
def Blenderfont() -> TeX:
    return ControlSequence("blenderfont", ())


@Registry.add
def Dinfont() -> TeX:
    return ControlSequence("dinfont", ())
