"""``\\AtBeginDocument`` / ``\\AtEndDocument`` lifecycle hooks."""

from pytex import (
    AtBeginDocument,
    AtEndDocument,
    Command,
    RenewCommand,
    TeX,
)
from pytex.model.raw import Raw
from pytex_komascript import (
    Appendix,
    BackMatter,
    FrontMatter,
    KomaOptions,
    MainMatter,
)
from pytex_komascript.model import Block


def at_begin_document_block(toc: bool) -> TeX:
    """``\\AtBeginDocument`` body: frontmatter -> title -> (toc) -> mainmatter."""
    parts: list[TeX] = [
        FrontMatter,
        Command("maketitle"),
        # The original .cls trick: parameter-text absorbs \setstretch and the
        # body is {1.0}. Preserved verbatim — no native primitive matches.
        Raw(
            "\\newpage\\def\\istitlepage=\\false\\setstretch{1.0}",
            escape_spaces=False,
            safe=False,
        ),
    ]
    if toc:
        parts.append(Command("tableofcontents"))
    parts.append(MainMatter)
    return AtBeginDocument(Block(*parts))


def at_end_document_block(
    has_glossary: bool, has_acronyms: bool, has_bibliography: bool
) -> TeX:
    """``\\AtEndDocument`` body: appendix + backmatter + glossaries + bib."""
    parts: list[TeX] = [
        Command("clearpage"),
        Appendix,
        KomaOptions("open=any"),
        BackMatter,
        Raw("\\cfoot*{}\\ohead*{}", escape_spaces=False, safe=False),
        Raw("\\noindent\\blenderfont", escape_spaces=False, safe=False),
    ]
    if has_glossary or has_acronyms:
        parts.append(Command("glsaddallunused"))
    if has_glossary:
        parts.append(RenewCommand("entryname", "Wort"))
        parts.append(Command("printglossary"))
    if has_acronyms:
        parts.append(RenewCommand("entryname", "Abkürzung"))
        opts = "type=\\acronymtype,title=Abkürzungen"
        parts.append(Command("printglossary", options=opts))
    if has_bibliography:
        parts.append(Command("makebib"))
    return AtEndDocument(Block(*parts))


__all__ = ["at_begin_document_block", "at_end_document_block"]
