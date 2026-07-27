"""Render a StuPa or AStA meeting protocol from Obsidian-flavored Markdown.

The protocol is an `HSRTReport`. A full HSRT title page carries the meeting
metadata as data lines. Agenda items become numbered sections. Protocol entries
(decisions, votes and action items) become HSRT colored boxes. An optional
signature block closes the document.
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

_PARSER = marko.Markdown(extensions=["gfm"])

_VARIANTS: dict[str, Variant] = {
    "stupa": Variant.STUPA,
    "asta": Variant.ASTA,
    "echo": Variant.ECHO,
}

# Title-page rows: the label, then the frontmatter keys to try. The
# single-value fields come first.
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
    """Convert an ISO `YYYY-MM-DD` date to the German `DD.MM.YYYY` form.

    Any other value stays unchanged.
    """
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
            # The time range follows the date when the frontmatter has one.
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
    """Build an `HSRTReport` from split protocol frontmatter and body.

    Args:
        variant: The HSRT variant, which selects the logos. When it is `None`,
            the variant comes from the `gremium` (committee) frontmatter key.
        title: The protocol title. When it is `None`, PyTeX composes the title
            from the committee and the date.
    """
    converter = ProtocolConverter(meta=meta, base_level=base_level)
    converted = converter.block(_PARSER.parse(body_md))
    # The signature block is optional. It follows the body when the
    # frontmatter lists `unterschriften` (signatures).
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
        # Agenda items are top-level `#` headings, so they become `\section`.
        # In scrbook a section without a chapter would number as "0.1". Number
        # the sections as agenda items instead, so a heading reads "TOP 1".
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
    """Convert a protocol Markdown string to an `HSRTReport`."""
    return render_protocol(text, base_level=base_level)


@Registry.add
def IncludeProtocol(path: str | Path, *, encoding: str = "utf-8") -> TeX:
    """Read a protocol Markdown file and convert it with `render_protocol`.

    Args:
        encoding: The text encoding of the file. The default is `utf-8`.
    """
    return render_protocol(Path(path).read_text(encoding=encoding))
