"""The :func:`HSRTReport` builder.

Reproduces the behaviour of the original ``HSRTReport.cls`` without defining a
LaTeX document class: a plain ``scrbook`` :class:`KomaDocument` is emitted with
a Python-built preamble. Every per-document decision the original class made
with ``\\strcompare`` / class options is taken in Python here, and every
preamble fragment is either a native :mod:`pytex` node or an
``IncludeTeX(...)`` of a small ``tex/`` asset.
"""

from collections.abc import Mapping
from pathlib import Path

from pytex import Acronyms, Glossary, Package, TeX
from pytex.model.raw import Raw
from pytex_komascript import KomaDocument
from pytex_komascript.document import DivValue
from pytex_komascript.model import Block

from .bibliography import (
    Backend,
    add_bib_resource,
    biblatex_package,
    bibliography_block,
    bibliography_packages,
    makebib_command,
)
from .colors import colors_block
from .config import (
    IMPORTS_PACKAGES,
    at_begin_document_block,
    at_end_document_block,
    cleveref_block,
    glossary_settings_block,
    hyperref_block,
    imports_block,
    page_setup_block,
    pagebreaks_block,
    path_defs_block,
    sections_block,
    toc_config_block,
    typography_block,
)
from .fonts import fonts_block
from .infoblocks import infoblocks_preamble
from .listings_setup import listings_packages, listings_setup_block
from .logos import logos_block
from .titlepage import title_metadata_block, title_page_defs
from .variants import Variant
from .watermark import watermark_block
from .wordcount import count_words


def _paper_option(paper_size: str) -> str:
    if "=" in paper_size or paper_size.endswith("paper"):
        return paper_size
    return f"paper={paper_size}"


def _default_assets_path() -> str:
    return str(Path(__file__).parent / "Assets")


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
    assets_path: str | None = None,
    koma_fonts: Mapping[str, str] | None = None,
) -> KomaDocument:
    """Build an HSRT report as a ``scrbook`` :class:`KomaDocument`."""
    body = content if isinstance(content, TeX) else Raw(content, escape_spaces=False)

    has_glossary = bool(glossary)
    has_acronyms = bool(acronyms)
    has_bibliography = bibliography is not None

    if assets_path is None:
        assets_path = _default_assets_path()

    # Title-page data (Python computes the wordcount line)
    data_lines = list(title_page_data or [])
    if wordcount:
        data_lines.append(("Wortanzahl", str(count_words(body))))

    # Logo resolution — used by both at-begin-page and the title-page redef
    logos_setup, resolved = logos_block(variant, logos, footer_logos)

    watermark_text = (
        watermark.serialize() if isinstance(watermark, TeX) else (watermark or "")
    )

    # ------------------------------------------------------------------
    # Package list
    # ------------------------------------------------------------------
    packages: set[Package | str] = set(IMPORTS_PACKAGES)
    packages.update(listings_packages())
    if has_bibliography:
        packages.add(biblatex_package(
            backend=bibliography_backend, style=bibliography_style
        ))
        packages.update(bibliography_packages())

    # ------------------------------------------------------------------
    # Preamble parts (in document order)
    # ------------------------------------------------------------------
    parts: list[TeX] = [
        path_defs_block(assets_path, variant),
        imports_block(),
        colors_block(),
        title_page_defs(resolved),
        makebib_command(),
        hyperref_block(),
    ]
    if has_bibliography:
        parts.append(bibliography_block())
    parts.extend(
        [
            fonts_block(),
            page_setup_block(),
            sections_block(),
            glossary_settings_block(),
            toc_config_block(),
            typography_block(),
            pagebreaks_block(),
            cleveref_block(),
            listings_setup_block(),
            logos_setup,
            infoblocks_preamble(),
            watermark_block(watermark_text),
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
        parts.append(glossary)
    if has_acronyms:
        parts.append(acronyms)
    if preamble is not None:
        parts.append(
            preamble if isinstance(preamble, TeX) else Raw(preamble, escape_spaces=False)
        )
    parts.append(at_begin_document_block(toc))
    parts.append(at_end_document_block(has_glossary, has_acronyms, has_bibliography))

    extra: list[str] = ["onecolumn" if one_column else "twocolumn"]
    if not two_side:
        extra.append("oneside")

    return KomaDocument(
        content=body,
        document_class="scrbook",
        preamble=Block(*parts),
        packages=packages,
        manage_packages=True,
        font_size=font_size,
        paper_size=_paper_option(paper_size),
        div=div,
        two_side=two_side,
        extra_class_options=extra,
        koma_fonts=koma_fonts,
    )
