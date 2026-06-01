"""Render a STUPA/AStA meeting protocol from Obsidian-flavoured Markdown.

The protocol is an :class:`~pytex_hsrtreport.document.HSRTReport` configured for
a short minutes document: no title page, a compact header block (built from the
frontmatter) at the top, agenda items as numbered sections, and protocol
entries (decisions, votes, action items) rendered as HSRT callout boxes.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import marko

from pytex.model.concat import Concat
from pytex.model.raw import Raw
from pytex.registry import Registry
from pytex_hsrtreport.document import HSRTReport
from pytex_hsrtreport.variants import Variant

from .convert import ProtocolConverter
from .frontmatter import FrontmatterValue, split_frontmatter
from .header import header_from_meta
from .signatures import signature_block_from_meta

if TYPE_CHECKING:
    from pytex.interface.tex import TeX

__all__ = ["IncludeProtocol", "Protocol", "render_protocol"]

_PARSER = marko.Markdown()

_VARIANTS: dict[str, Variant] = {
    "stupa": Variant.STUPA,
    "asta": Variant.ASTA,
    "echo": Variant.ECHO,
}


def _variant(meta: dict[str, FrontmatterValue]) -> Variant:
    gremium = meta.get("gremium", "")
    key = gremium.lower().strip() if isinstance(gremium, str) else ""
    return _VARIANTS.get(key, Variant.STUPA)


def _document_title(meta: dict[str, FrontmatterValue]) -> str:
    gremium = meta.get("gremium")
    datum = meta.get("datum")
    head = (
        f"{gremium} — Protokoll"
        if isinstance(gremium, str) and gremium
        else "Protokoll"
    )
    return f"{head} ({datum})" if isinstance(datum, str) and datum else head


def render_protocol(text: str, *, base_level: int = 0) -> HSRTReport:
    """Build an `HSRTReport` from the Markdown source of a protocol."""
    meta, body_md = split_frontmatter(text)
    converter = ProtocolConverter(meta=meta, base_level=base_level)
    converted = converter.block(_PARSER.parse(body_md))
    header = header_from_meta(meta)
    # Optional sign-off block, appended when the frontmatter lists `unterschriften`.
    signatures = signature_block_from_meta(meta)
    tail = (Raw("\n\n"), signatures) if signatures is not None else ()
    return HSRTReport(
        variant=_variant(meta),
        document_class="scrbook",
        show_titlepage=False,
        show_toc=False,
        show_footer_logos=True,
        title=_document_title(meta),
        # Agenda items are top-level `#` headings -> \section. In scrbook a
        # chapterless section would number as "0.1"; flatten it to a plain
        # arabic counter so TOPs read 1, 2, 3, ...
        user_preamble=Raw(r"\renewcommand*{\thesection}{\arabic{section}}"),
        body=Concat(header, Raw("\n\n"), converted, *tail),
    )


@Registry.add
def Protocol(text: str, *, base_level: int = 0) -> TeX:
    """Convert a protocol Markdown string to a renderable `HSRTReport`."""
    return render_protocol(text, base_level=base_level)


@Registry.add
def IncludeProtocol(path: str | Path, *, encoding: str = "utf-8") -> TeX:
    """Read a protocol Markdown file and render it (see :func:`render_protocol`)."""
    return render_protocol(Path(path).read_text(encoding=encoding))
