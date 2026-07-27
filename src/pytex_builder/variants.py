"""The variants for a Markdown input file.

A variant maps a Markdown source to a concrete document:

* `plain` - a bare `Document` that wraps the converted Markdown.
* `report` - an HSRT report with a title page and a table of contents.
* `report-makers` - an HSRT report with the MAKERS logo on the title page and
  in the footer of every page.
* `protocol-asta` - an AStA meeting protocol. It is an HSRT report with the
  AStA logos.
* `protocol-stupa` - a StuPa meeting protocol. It is an HSRT report with the
  StuPa logos.

You pick the variant with `pytex --variant <name>`. Without that option PyTeX
detects the variant. It picks a protocol variant when the frontmatter looks
like a meeting protocol, and `plain` otherwise.

Document-class parameters come from the YAML frontmatter and from the
`--config` JSON, and `--config` overrides the frontmatter. For a variant with a
title page, the title falls back to the first `#` heading of the document when
neither source gives one.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from pytex.commands.biblatex import Addbibresource
from pytex.commands.builtin import ChapterStar
from pytex.model.concat import Concat
from pytex.model.document import Document
from pytex.model.empty import Empty
from pytex.model.raw import Raw
from pytex_hsrtreport.document import HSRTReport
from pytex_hsrtreport.titlepage import TitlePageDataLine
from pytex_hsrtreport.variants import Variant
from pytex_markdown import Markdown, escape_latex, split_frontmatter
from pytex_markdown.protocol import build_protocol

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pytex.interface.package import PackageOption
    from pytex.interface.tex import TeX
    from pytex_markdown.frontmatter import FrontmatterValue

__all__ = ["VARIANT_NAMES", "build_document"]

VARIANT_NAMES: tuple[str, ...] = (
    "plain",
    "report",
    "report-makers",
    "protocol-asta",
    "protocol-stupa",
)

type Options = Mapping[str, object]

_H1_RE = re.compile(r"^#\s+(.+?)\s*#*\s*$")
_HEADING_RE = re.compile(r"^(#{1,6})\s")


def build_document(
    text: str,
    *,
    variant: str | None = None,
    config: Mapping[str, object] | None = None,
) -> TeX:
    """Convert the Markdown `text` into a document.

    Args:
        variant: The variant name. `None` lets PyTeX detect the variant from
            the frontmatter.
        config: Document-class parameters that override the frontmatter.

    Raises:
        ValueError: `variant` is not a known variant name.
    """
    meta, body = split_frontmatter(text)
    options: dict[str, object] = {**meta, **(config or {})}

    if variant is None:
        return _auto(meta, body, options)
    if variant == "plain":
        return _plain(body, options)
    if variant == "report":
        return _report(body, options)
    if variant == "report-makers":
        return _report(body, options, logo_variant=Variant.MAKERS, footer_logos=True)
    if variant == "protocol-asta":
        return _protocol(meta, body, options, force=Variant.ASTA)
    if variant == "protocol-stupa":
        return _protocol(meta, body, options, force=Variant.STUPA)
    raise ValueError(f"unknown variant {variant!r}; choose from {VARIANT_NAMES}")


def _auto(
    meta: Mapping[str, FrontmatterValue], body: str, options: dict[str, object]
) -> TeX:
    if "gremium" in options or options.get("typ") == "protokoll":
        return _protocol(meta, body, options, force=None)
    return _plain(body, options)


# -- builders --------------------------------------------------------------


def _plain(body: str, options: dict[str, object]) -> TeX:
    return Document(
        body=Markdown(body),
        document_class=_str(options, "documentclass", "document_class", "class")
        or "article",
        document_class_options=_class_options(options),
    )


def _report(
    body: str,
    options: dict[str, object],
    *,
    logo_variant: Variant = Variant.INF,
    footer_logos: bool = False,
) -> TeX:
    title = _str(options, "title", "titel")
    derived = False
    if title is None:
        title, body = _derive_title(body)
        derived = title is not None
    body_tex: TeX = Markdown(body, base_level=_report_base_level(body))
    if derived and title is not None:
        # `_derive_title` took the `#` heading out of the body for the title
        # page. Put it back at the top of the body as an unnumbered chapter
        # heading, so the reader still sees it.
        body_tex = Concat(ChapterStar(escape_latex(title)), Raw("\n\n"), body_tex)
    bibliography = _bibliography(options)
    return HSRTReport(
        variant=logo_variant,
        show_titlepage=title is not None,
        show_footer_logos=footer_logos,
        show_toc=True,
        show_bibliography=bibliography is not None,
        user_preamble=_bib_preamble(bibliography) if bibliography else Empty,
        title=escape_latex(title) if title is not None else None,
        author=_escaped(_str(options, "author", "autor")),
        abstract=_escaped(_str(options, "abstract", "zusammenfassung")),
        keywords=_escaped(_keywords(options)),
        abstract_heading=_escaped(
            _str(options, "abstract_heading", "abstract_title", "zusammenfassung_titel")
        )
        or "Abstract",
        keywords_heading=_escaped(
            _str(options, "keywords_heading", "keywords_title", "schlagworte_titel")
        )
        or "Keywords",
        data_lines=_data_lines(options),
        logos=_logos(options),
        # `body_tex` maps the shallowest heading level in the body to
        # `\chapter`, so the deeper headings nest under it. A document whose top
        # level is `##`, because `#` became the title, needs this mapping.
        # Without it the sections get no chapter and take the numbers 0.x.
        body=body_tex,
        document_class_options=_class_options(options),
    )


def _report_base_level(body: str) -> int:
    """Return the heading shift that maps the shallowest heading to `\\chapter`.

    Returns:
        The shift for the `base_level` argument of `Markdown`. A body without a
        heading gives `-1`.
    """
    levels = [len(m.group(1)) for m in map(_HEADING_RE.match, body.splitlines()) if m]
    return -min(levels) if levels else -1


def _protocol(
    meta: Mapping[str, FrontmatterValue],
    body: str,
    options: dict[str, object],
    *,
    force: Variant | None,
) -> TeX:
    title = _str(options, "title", "titel")
    return build_protocol(
        meta,
        body,
        variant=force,
        title=escape_latex(title) if title is not None else None,
    )


# -- helpers ---------------------------------------------------------------

# The name of the `.bib` file that `filecontents` writes next to the rendered
# `.tex` file. biber then finds it in the build directory, and the document
# needs no external file path.
_BIB_FILENAME = "pytex-md-refs.bib"


def _bibliography(options: Mapping[str, object]) -> str | None:
    """Return the BibTeX content from the `bibliography` frontmatter key.

    The value is either inline BibTeX or a path to a `.bib` file. PyTeX treats
    the value as inline BibTeX when it holds an `@` entry. Otherwise PyTeX
    reads the file.

    Returns:
        The BibTeX text. The result is `None` when no key holds a value, or
        when the path does not name a file.
    """
    value = _str(options, "bibliography", "literatur", "bibliografie", "bib")
    if value is None:
        return None
    if "@" in value:
        return value
    path = Path(value)
    return path.read_text(encoding="utf-8") if path.is_file() else None


def _resolve_logo(item: str) -> str:
    """Resolve one logo entry.

    A vendored logo name passes through unchanged. A path to a file becomes an
    absolute path. The compile pass runs in the build directory, and a relative
    path would not resolve there.
    """
    candidate = Path(item).expanduser()
    return str(candidate.resolve()) if candidate.is_file() else item


def _logos(options: Mapping[str, object]) -> tuple[str, ...] | None:
    """Return the title-page logos from the `logos` or `logo` frontmatter key.

    Each entry is a vendored logo name, for example `INF` or `MAKERS`, or a
    path to a custom image. The value is a list or a single scalar.

    Returns:
        The logo entries, or `None` when neither key holds a usable value.
    """
    raw = options.get("logos", options.get("logo"))
    if isinstance(raw, list):
        items = [str(item) for item in raw]  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
    elif isinstance(raw, str) and raw:
        items = [raw]
    else:
        return None
    return tuple(_resolve_logo(item) for item in items)


def _bib_preamble(content: str) -> TeX:
    """Return the preamble that embeds the bibliography and loads it.

    The preamble writes the `.bib` file with `filecontents` and then calls
    `\\addbibresource`. This keeps the document self-contained. The `.bib` file
    lands in the build directory during the compile pass, so biber resolves it
    without a separate path. The numeric biblatex default style applies.
    """
    block = (
        f"\\begin{{filecontents*}}[overwrite,noheader]{{{_BIB_FILENAME}}}\n"
        + content.rstrip("\n")
        + "\n\\end{filecontents*}\n"
    )
    return Concat(Raw(block, allow_replacements=False), Addbibresource(_BIB_FILENAME))


def _str(options: Mapping[str, object], *keys: str) -> str | None:
    for key in keys:
        value = options.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _escaped(value: str | None) -> str | None:
    return escape_latex(value) if value is not None else None


def _keywords(options: Mapping[str, object]) -> str | None:
    """Return the title-page keywords from `keywords` or `schlagworte`.

    Returns:
        The keywords as one comma-separated string, or `None`. A list value
        becomes a comma-separated string.
    """
    for key in ("keywords", "schlagworte"):
        value = options.get(key)
        if isinstance(value, list) and value:
            return ", ".join(str(item) for item in value)  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
        if isinstance(value, str) and value:
            return value
    return None


def _data_lines(options: Mapping[str, object]) -> tuple[TitlePageDataLine, ...]:
    """Return the title-page data table from `datalines` or `data`.

    Each entry is a `"Label: value"` string, because frontmatter has no nested
    maps. The value is a block list, a flow list, or a single scalar. PyTeX
    skips an entry without a colon.
    """
    raw = options.get("datalines", options.get("data"))
    if isinstance(raw, list):
        items = [str(item) for item in raw]  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
    elif isinstance(raw, str) and raw:
        items = [raw]
    else:
        return ()
    partitioned = (item.partition(":") for item in items)
    return tuple(
        TitlePageDataLine(escape_latex(label.strip()), escape_latex(value.strip()))
        for label, sep, value in partitioned
        if sep and label.strip()
    )


def _derive_title(body: str) -> tuple[str | None, str]:
    """Take the first ATX `#` heading out of `body` and use it as the title.

    Returns:
        The title and the body. The title is `None` when the body has no `#`
        heading. The returned body has that heading line removed, so it does
        not also render as a chapter.
    """
    lines = body.splitlines()
    for index, line in enumerate(lines):
        match = _H1_RE.match(line)
        if match is not None:
            del lines[index]
            return match.group(1).strip(), "\n".join(lines)
    return None, body


def _class_options(options: Mapping[str, object]) -> set[PackageOption]:
    """Return the class options from the `classoptions` frontmatter key.

    The value is a list, a dict, or one comma-separated string.
    """
    raw = options.get("classoptions", options.get("class_options"))
    result: set[PackageOption] = set()
    if isinstance(raw, dict):
        result.update((str(k), str(v)) for k, v in raw.items())  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
    elif isinstance(raw, list):
        result.update(_option(item) for item in raw)  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
    elif isinstance(raw, str):
        result.update(_option(item.strip()) for item in raw.split(",") if item.strip())
    return result


def _option(item: object) -> PackageOption:
    if isinstance(item, str) and "=" in item:
        key, _, value = item.partition("=")
        return (key.strip(), value.strip())
    return str(item)
