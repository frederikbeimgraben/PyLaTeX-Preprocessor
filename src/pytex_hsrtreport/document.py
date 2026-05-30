"""The :func:`HSRTReport` builder.

Reproduces the behaviour of the original ``HSRTReport.cls`` without defining a
LaTeX document class: a plain ``scrbook`` :class:`KomaDocument` is emitted
with a Python-built preamble. Per-document branching that the original .cls
expressed with ``\\strcompare`` / class options happens in Python; every
preamble fragment is a :mod:`pytex` / :mod:`pytex_tikz` native node — no
``.tex`` assets are bundled with the package.

Package collection: only packages with non-default options are passed to
``KomaDocument`` explicitly; every other ``\\usepackage`` line is discovered
by walking the TeX tree's ``required_packages`` and resolved (including
conflict detection) by :mod:`pytex.library.packages`.
"""

from collections.abc import Mapping

from pytex import Acronyms, Glossary, NewCommand, Package, TeX
from pytex.model.raw import Raw
from pytex_komascript import KomaDocument
from pytex_komascript.document import DivValue
from pytex_komascript.model import Block

from .bibliography import (
    AddBibResourceCmd,
    Backend,
    BiblatexPackage,
    BibliographyBlock,
    BibliographyPackages,
    MakebibCommand,
)
from .colors import ColorsBlock
from .fonts import FontsBlock
from .logos import DEFAULT_GLOBAL_SCALE, DEFAULT_MAIN_SCALE, LogosBlock
from .preamble import (
    PACKAGES_WITH_OPTIONS,
    AtBeginDocumentBlock,
    AtEndDocumentBlock,
    CleverefBlock,
    GlossarySettingsBlock,
    HyperrefBlock,
    ImportsBlock,
    PagebreaksBlock,
    PageSetupBlock,
    SectionsBlock,
    TocConfigBlock,
    TypographyBlock,
)
from .titlepage import TitlePageDefs
from .variants import Variant
from .watermark import WatermarkBlock
from .wordcount import count_words


def _PaperOption(paper_size: str) -> str:
    if "=" in paper_size or paper_size.endswith("paper"):
        return paper_size
    return f"paper={paper_size}"


def _Body(content: TeX | str) -> TeX:
    return content if isinstance(content, TeX) else Raw(content, escape_spaces=False)


def _DataLines(
    title_page_data: "list[tuple[str, TeX | str]] | None",
    body: TeX,
    *,
    wordcount: bool,
) -> tuple[tuple[str, TeX | str], ...]:
    rows = tuple(title_page_data or ())
    if wordcount:
        rows = (*rows, ("Wortanzahl", str(count_words(body))))
    return rows


def _ExtraClassOptions(*, one_column: bool, two_side: bool) -> list[str]:
    return [
        "onecolumn" if one_column else "twocolumn",
        *(("oneside",) if not two_side else ()),
    ]


def _OptionalUserPreamble(preamble: TeX | str | None) -> tuple[TeX, ...]:
    if preamble is None:
        return ()
    return (
        preamble if isinstance(preamble, TeX) else Raw(preamble, escape_spaces=False),
    )


def HSRTReport(
    content: TeX | str,
    *,
    preamble: TeX | str | None = None,
    abstract: TeX | str | None = None,
    keywords: TeX | str | None = None,
    title: TeX | str | None = None,
    author: TeX | str | None = None,
    created_on: str | None = None,
    module_name: str | None = None,
    title_page_data: "list[tuple[str, TeX | str]] | None" = None,
    font_size: str = "11pt",
    paper_size: str = "a4",
    div: DivValue = 20,
    two_side: bool = False,
    one_column: bool = True,
    logos: "set[str] | list[str] | tuple[str, ...] | dict[str, float] | None" = None,
    watermark: TeX | str | None = None,
    variant: Variant = "INF_meti",
    glossary: Glossary | None = None,
    acronyms: Acronyms | None = None,
    bibliography: str | None = None,
    bibliography_backend: Backend = "bibtex",
    bibliography_style: str = "ieee",
    toc: bool = False,
    footer_logos: bool = False,
    wordcount: bool = False,
    logos_scale: float = DEFAULT_GLOBAL_SCALE,
    main_logo_scale: float = DEFAULT_MAIN_SCALE,
    koma_fonts: Mapping[str, str] | None = None,
) -> KomaDocument:
    """Build an HSRT report as a ``scrbook`` :class:`KomaDocument`."""
    body = _Body(content)
    has_bibliography = bibliography is not None

    data_lines = _DataLines(title_page_data, body, wordcount=wordcount)

    logos_setup, resolved = LogosBlock(
        variant,
        logos,
        footer_logos,
        global_scale=logos_scale,
        main_scale=main_logo_scale,
    )

    watermark_text = (
        watermark.serialize() if isinstance(watermark, TeX) else (watermark or "")
    )

    packages: set[Package | str] = set(PACKAGES_WITH_OPTIONS)
    if has_bibliography:
        packages.add(
            BiblatexPackage(backend=bibliography_backend, style=bibliography_style)
        )
        packages |= BibliographyPackages()

    return KomaDocument(
        content=body,
        document_class="scrbook",
        preamble=Block(
            ImportsBlock(),
            ColorsBlock(),
            TitlePageDefs(
                resolved,
                title=title,
                author=author,
                created_on=created_on,
                abstract=abstract,
                keywords=keywords,
                data_lines=data_lines,
                global_scale=logos_scale,
                main_scale=main_logo_scale,
            ),
            *(
                (NewCommand("modulename", module_name),)
                if module_name is not None
                else ()
            ),
            MakebibCommand(),
            HyperrefBlock(),
            *((BibliographyBlock(),) if has_bibliography else ()),
            FontsBlock(),
            PageSetupBlock(),
            SectionsBlock(),
            GlossarySettingsBlock(),
            TocConfigBlock(),
            TypographyBlock(),
            PagebreaksBlock(),
            CleverefBlock(),
            logos_setup,
            WatermarkBlock(watermark_text),
            *((AddBibResourceCmd(bibliography),) if bibliography is not None else ()),
            *((glossary,) if glossary is not None else ()),
            *((acronyms,) if acronyms is not None else ()),
            *_OptionalUserPreamble(preamble),
            AtBeginDocumentBlock(toc),
            AtEndDocumentBlock(
                has_glossary=glossary is not None,
                has_acronyms=acronyms is not None,
                has_bibliography=has_bibliography,
            ),
        ),
        packages=packages | {"bophook"},
        manage_packages=True,
        font_size=font_size,
        paper_size=_PaperOption(paper_size),
        div=div,
        two_side=two_side,
        extra_class_options=_ExtraClassOptions(
            one_column=one_column, two_side=two_side
        ),
        koma_fonts=koma_fonts,
    )
