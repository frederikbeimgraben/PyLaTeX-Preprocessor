"""The :func:`HSRTReport` builder.

Reproduces the behaviour of the original ``HSRTReport.cls`` without defining a
LaTeX document class: a plain ``scrbook`` document is emitted together with the
full preamble (all configuration modules), and every decision the class made
with ``\\strcompare``/options is taken in Python here. Returns a
:class:`pytex_komascript.KomaDocument`.
"""

from collections.abc import Mapping

from pytex import Acronyms, Glossary, TeX
from pytex.model.raw import Raw
from pytex_komascript import KomaDocument
from pytex_komascript.document import DivValue

from .bibliography import (
    Backend,
    MAKEBIB,
    add_bib_resource,
    bibliography_config,
)
from .colors import colors_block
from .config import (
    CLEVEREF,
    GLOSSARY_SETTINGS,
    HYPERREF,
    IMPORTS,
    PAGEBREAKS,
    PAGESETUP,
    SECTIONS,
    TOC_CONFIG,
    TYPOGRAPHY,
)
from .fonts import FONTS
from .infoblocks import INFOBLOCKS_PREAMBLE
from .listings_setup import LISTINGS_SETUP
from .logos import logos_block
from .titlepage import TITLEPAGE_DEFS, title_metadata_block
from .variants import Variant
from .watermark import watermark_block
from .wordcount import count_words


def _atletter(body: str) -> str:
    return f"\\makeatletter\n{body}\n\\makeatother"


def _paper_option(paper_size: str) -> str:
    if "=" in paper_size or paper_size.endswith("paper"):
        return paper_size
    return f"paper={paper_size}"


def _path_defs(assets_path: str) -> str:
    return (
        f"\\def\\classPath{{{assets_path}}}\n"
        r"\def\fontsPath{\classPath/Assets/Fonts}"
        "\n"
        r"\def\imagesPath{\classPath/Assets/Images}"
        "\n"
        r"\providecommand{\ReportVariant}{meti}"
    )


def _at_begin_document(toc: bool) -> str:
    toc_line = r"  \tableofcontents" + "\n" if toc else ""
    return (
        r"\AtBeginDocument{"
        "\n"
        r"  \frontmatter"
        "\n"
        r"  \maketitle"
        "\n"
        r"  \newpage\def\istitlepage=\false\setstretch{1.0}"
        "\n"
        f"{toc_line}"
        r"  \mainmatter"
        "\n"
        r"}"
    )


def _at_end_document(
    has_glossary: bool, has_acronyms: bool, has_bibliography: bool
) -> str:
    parts = [
        r"\AtEndDocument{",
        r"  \clearpage\appendix\backmatter",
        r"  \cfoot*{}\ohead*{}",
        r"  \noindent\blenderfont",
    ]
    if has_glossary or has_acronyms:
        parts.append(r"  \glsaddallunused")
    if has_glossary:
        parts.append(r"  \renewcommand*{\entryname}{Wort}\clearpage\printglossary")
    if has_acronyms:
        parts.append(
            r"  \renewcommand*{\entryname}{Abkürzung}\clearpage\printglossary[type=\acronymtype,title=Abkürzungen]"
        )
    if has_bibliography:
        parts.append(r"  \makebib")
    parts.append(r"}")
    return "\n".join(parts)


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
    assets_path: str = "HSRTReport",
    koma_fonts: Mapping[str, str] | None = None,
) -> KomaDocument:
    """Build an HSRT report as a ``scrbook`` :class:`KomaDocument`.

    See the module docstring; falsy ``glossary``/``acronyms``/``bibliography``
    disable those features. ``logos`` overrides the ``variant`` default set.
    """
    body = content if isinstance(content, TeX) else Raw(content, escape_spaces=False)

    has_glossary = bool(glossary)
    has_acronyms = bool(acronyms)
    has_bibliography = bibliography is not None

    data_lines = list(title_page_data or [])
    if wordcount:
        data_lines.append(("Wortanzahl", str(count_words(body))))

    parts: list[str] = [
        _path_defs(assets_path),
        IMPORTS,
        colors_block(),
        _atletter(TITLEPAGE_DEFS),
        MAKEBIB,
        HYPERREF,
    ]
    if has_bibliography:
        parts.append(
            bibliography_config(bibliography_backend, bibliography_style)
        )
    parts.extend(
        [
            FONTS,
            _atletter(PAGESETUP),
            SECTIONS,
            GLOSSARY_SETTINGS,
            _atletter(TOC_CONFIG),
            _atletter(TYPOGRAPHY),
            PAGEBREAKS,
            CLEVEREF,
            LISTINGS_SETUP,
            logos_block(variant, logos, footer_logos),
            INFOBLOCKS_PREAMBLE,
            watermark_block(
                watermark.serialize()
                if isinstance(watermark, TeX)
                else (watermark or "")
            ),
            title_metadata_block(
                title=title,
                author=author,
                created_on=created_on,
                abstract=abstract,
                keywords=keywords,
                module_name=module_name,
                data_lines=data_lines,
            ),
        ]
    )
    if has_bibliography:
        parts.append(add_bib_resource(bibliography))
    if has_glossary:
        parts.append(glossary.serialize())
    if has_acronyms:
        parts.append(acronyms.serialize())
    if preamble is not None:
        parts.append(
            preamble.serialize()
            if isinstance(preamble, TeX)
            else str(preamble)
        )
    parts.append(_at_begin_document(toc))
    parts.append(_at_end_document(has_glossary, has_acronyms, has_bibliography))

    preamble_block = Raw("\n\n".join(parts), escape_spaces=False, safe=False)

    extra: list[str] = ["onecolumn" if one_column else "twocolumn"]
    if not two_side:
        extra.append("oneside")

    return KomaDocument(
        content=body,
        document_class="scrbook",
        preamble=preamble_block,
        manage_packages=False,
        font_size=font_size,
        paper_size=_paper_option(paper_size),
        div=div,
        two_side=two_side,
        extra_class_options=extra,
        koma_fonts=koma_fonts,
    )
