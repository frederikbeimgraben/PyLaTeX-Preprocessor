"""``\\AtBeginDocument`` / ``\\AtEndDocument`` lifecycle hooks."""

from pytex import (
    AtBeginDocument,
    AtEndDocument,
    Command,
    Def,
    RenewCommand,
    TeX,
)
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
        Command("newpage"),
        # Original .cls trick: \def\istitlepage=\false\setstretch{1.0} — the
        # delimited param text swallows the \setstretch invocation.
        Def("istitlepage", "1.0", param_text="=\\false\\setstretch"),
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
        Command("cfoot*", ""),
        Command("ohead*", ""),
        Command("noindent"),
        Command("blenderfont"),
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
