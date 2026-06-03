"""Render a STUPA/AStA meeting protocol from Obsidian-flavoured Markdown.

The protocol is an :class:`~pytex_hsrtreport.document.HSRTReport`: a full HSRT
title page carries the meeting metadata as data lines, agenda items become
numbered sections, and protocol entries (decisions, votes, action items) render
as HSRT callout boxes. An optional signature block closes the document.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

import marko

from pytex.model.concat import Concat
from pytex.model.raw import Raw
from pytex.registry import Registry
from pytex_hsrtreport.document import HSRTReport
from pytex_hsrtreport.titlepage import TitlePageDataLine
from pytex_hsrtreport.variants import Variant

from ..frontmatter import FrontmatterValue, split_frontmatter
from .convert import ProtocolConverter
from .signatures import signature_block_from_meta

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pytex.interface.tex import TeX

__all__ = ["IncludeProtocol", "Protocol", "build_protocol", "render_protocol"]

_PARSER = marko.Markdown()

_VARIANTS: dict[str, Variant] = {
    "stupa": Variant.STUPA,
    "asta": Variant.ASTA,
    "echo": Variant.ECHO,
}

# Title-page rows: (label, frontmatter keys to try), single-value fields first.
_SCALAR_ROWS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Datum", ("datum", "date")),
    ("Ort", ("ort",)),
    ("Sitzungsleitung", ("sitzungsleitung",)),
    ("Protokoll", ("protokoll",)),
)
_LIST_ROWS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Anwesend", ("anwesend",)),
    ("Entschuldigt", ("entschuldigt",)),
    ("Abwesend", ("abwesend",)),
    ("Gäste", ("gaeste", "gäste")),
)


def _scalar(meta: Mapping[str, FrontmatterValue], *keys: str) -> str:
    for key in keys:
        value = meta.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def _joined(meta: Mapping[str, FrontmatterValue], *keys: str) -> str:
    for key in keys:
        value = meta.get(key)
        if isinstance(value, list) and value:
            return ", ".join(value)
        if isinstance(value, str) and value:
            return value
    return ""


def _variant(meta: Mapping[str, FrontmatterValue]) -> Variant:
    return _VARIANTS.get(_scalar(meta, "gremium").lower(), Variant.STUPA)


def _format_date(value: str) -> str:
    """ISO ``YYYY-MM-DD`` -> German ``DD.MM.YYYY``; anything else is kept as-is."""
    match = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", value)
    return f"{match[3]}.{match[2]}.{match[1]}" if match else value


def _title(meta: Mapping[str, FrontmatterValue]) -> str:
    gremium = _scalar(meta, "gremium")
    datum = _format_date(_scalar(meta, "datum", "date"))
    if gremium and datum:
        return f"Protokoll der Sitzung des {gremium} vom {datum}"
    if gremium:
        return f"Protokoll der Sitzung des {gremium}"
    return "Sitzungsprotokoll"


def _data_lines(meta: Mapping[str, FrontmatterValue]) -> tuple[TitlePageDataLine, ...]:
    lines: list[TitlePageDataLine] = []
    for label, keys in _SCALAR_ROWS:
        value = _scalar(meta, *keys)
        if value:
            lines.append(TitlePageDataLine(label, value))
        if label == "Datum":
            # Append the time range right after the date when present.
            span = " – ".join(  # noqa: RUF001 (EN DASH between start/end)
                t
                for t in (
                    _scalar(meta, "beginn", "start"),
                    _scalar(meta, "ende", "end"),
                )
                if t
            )
            if span:
                lines.append(TitlePageDataLine("Zeit", span))
    for label, keys in _LIST_ROWS:
        value = _joined(meta, *keys)
        if value:
            lines.append(TitlePageDataLine(f"{label} ({value.count(',') + 1})", value))
    return tuple(lines)


def build_protocol(
    meta: Mapping[str, FrontmatterValue],
    body_md: str,
    *,
    base_level: int = 0,
    variant: Variant | None = None,
    title: str | None = None,
) -> HSRTReport:
    """Build an `HSRTReport` from already-split protocol frontmatter and body.

    `variant` overrides the gremium-derived HSRT variant (logos); `title`
    overrides the auto-composed protocol title.
    """
    converter = ProtocolConverter(meta=meta, base_level=base_level)
    converted = converter.block(_PARSER.parse(body_md))
    # Optional sign-off block, appended when the frontmatter lists `unterschriften`.
    signatures = signature_block_from_meta(meta)
    tail = (Raw("\n\n"), signatures) if signatures is not None else ()
    return HSRTReport(
        variant=variant or _variant(meta),
        document_class="scrbook",
        show_titlepage=True,
        show_toc=False,
        show_footer_logos=True,
        title=title or _title(meta),
        data_lines=_data_lines(meta),
        # Agenda items are top-level `#` headings -> \section. In scrbook a
        # chapterless section would number as "0.1"; number them as agenda
        # items instead, so headings read "TOP 1", "TOP 2", ...
        user_preamble=Raw(r"\renewcommand*{\thesection}{TOP~\arabic{section}}"),
        body=Concat(converted, *tail),
    )


def render_protocol(
    text: str, *, base_level: int = 0, variant: Variant | None = None
) -> HSRTReport:
    """Build an `HSRTReport` from the Markdown source of a protocol."""
    meta, body_md = split_frontmatter(text)
    return build_protocol(meta, body_md, base_level=base_level, variant=variant)


@Registry.add
def Protocol(text: str, *, base_level: int = 0) -> TeX:
    """Convert a protocol Markdown string to a renderable `HSRTReport`."""
    return render_protocol(text, base_level=base_level)


@Registry.add
def IncludeProtocol(path: str | Path, *, encoding: str = "utf-8") -> TeX:
    """Read a protocol Markdown file and render it (see :func:`render_protocol`)."""
    return render_protocol(Path(path).read_text(encoding=encoding))
