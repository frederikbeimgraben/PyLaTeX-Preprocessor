"""``\\AtBeginDocument`` / ``\\AtEndDocument`` lifecycle hooks."""

from pytex import (
    AtBeginDocument,
    AtEndDocument,
    Command,
    Def,
    Raw,
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


def AtBeginDocumentBlock(toc: bool) -> TeX:
    """``\\AtBeginDocument`` body: frontmatter -> title -> (toc) -> mainmatter."""
    return AtBeginDocument(
        Block(
            FrontMatter,
            Command("maketitle"),
            Command("newpage"),
            # Original .cls trick: \def\istitlepage=\false\setstretch{1.0} —
            # the delimited param text swallows the \setstretch invocation.
            Def("istitlepage", "1.0", param_text="=\\false\\setstretch"),
            *((Command("tableofcontents"),) if toc else ()),
            MainMatter,
        )
    )


def _Glossary() -> TeX:
    return Block(
        RenewCommand("entryname", "Wort"),
        Command("printglossary"),
    )


def _Acronyms() -> TeX:
    return Block(
        RenewCommand("entryname", "Abkürzung"),
        Raw(
            "\\printglossary[type=\\acronymtype,title=Abkürzungen]",
            escape_spaces=False,
            safe=False,
        ),
    )


def AtEndDocumentBlock(
    *,
    has_glossary: bool,
    has_acronyms: bool,
    has_bibliography: bool,
) -> TeX:
    """``\\AtEndDocument`` body: appendix + backmatter + glossaries + bib."""
    return AtEndDocument(
        Block(
            Command("clearpage"),
            Appendix,
            KomaOptions("open=any"),
            BackMatter,
            Command("cfoot*", ""),
            Command("ohead*", ""),
            Command("noindent"),
            Command("blenderfont"),
            *((Command("glsaddallunused"),) if has_glossary or has_acronyms else ()),
            *((_Glossary(),) if has_glossary else ()),
            *((_Acronyms(),) if has_acronyms else ()),
            *((Command("makebib"),) if has_bibliography else ()),
        )
    )


__all__ = ["AtBeginDocumentBlock", "AtEndDocumentBlock"]
