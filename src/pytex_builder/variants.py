"""Output styles for Markdown inputs.

A *variant* maps a Markdown source to a concrete document:

* ``plain``          - a bare ``Document`` wrapping the converted Markdown.
* ``report``         - an HSRT report with title page and table of contents.
* ``protocol-asta``  - an AStA meeting protocol (HSRT report, AStA logos).
* ``protocol-stupa`` - a StuPa meeting protocol (HSRT report, StuPa logos).

The variant is chosen with ``pytex --variant <name>``; without it the builder
auto-detects (protocol when the frontmatter looks like a meeting protocol,
otherwise plain). Document-class parameters come from the YAML frontmatter and
from ``--config`` JSON (which overrides the frontmatter).

For styles with a title page, the title falls back to the first ``#`` heading
of the document when it is not given via frontmatter/config.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from pytex.commands.builtin import ChapterStar
from pytex.model.concat import Concat
from pytex.model.document import Document
from pytex.model.raw import Raw
from pytex_hsrtreport.document import HSRTReport
from pytex_hsrtreport.variants import Variant
from pytex_markdown import Markdown, escape_latex
from pytex_protocol.document import build_protocol
from pytex_protocol.frontmatter import split_frontmatter

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pytex.interface.package import PackageOption
    from pytex.interface.tex import TeX
    from pytex_protocol.frontmatter import FrontmatterValue

__all__ = ["VARIANT_NAMES", "build_document"]

VARIANT_NAMES: tuple[str, ...] = ("plain", "report", "protocol-asta", "protocol-stupa")

type Options = Mapping[str, object]

_H1_RE = re.compile(r"^#\s+(.+?)\s*#*\s*$")
_HEADING_RE = re.compile(r"^(#{1,6})\s")


def build_document(
    text: str,
    *,
    variant: str | None = None,
    config: Mapping[str, object] | None = None,
) -> TeX:
    """Convert Markdown `text` to a document using the given (or detected) style."""
    meta, body = split_frontmatter(text)
    options: dict[str, object] = {**meta, **(config or {})}

    if variant is None:
        return _auto(meta, body, options)
    if variant == "plain":
        return _plain(body, options)
    if variant == "report":
        return _report(body, options)
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


def _report(body: str, options: dict[str, object]) -> TeX:
    title = _str(options, "title", "titel")
    derived = False
    if title is None:
        title, body = _derive_title(body)
        derived = title is not None
    body_tex: TeX = Markdown(body, base_level=_report_base_level(body))
    if derived and title is not None:
        # The `#` heading was pulled out for the title page; re-emit it at the
        # top of the body as a big, unnumbered heading so it is not lost.
        body_tex = Concat(ChapterStar(escape_latex(title)), Raw("\n\n"), body_tex)
    return HSRTReport(
        variant=Variant.INF,
        show_titlepage=title is not None,
        show_toc=True,
        title=escape_latex(title) if title is not None else None,
        author=_escaped(_str(options, "author", "autor")),
        # Map the shallowest heading in the body to \chapter, so headings nest
        # under it. Without this, a doc whose top level is `##` (because `#` was
        # consumed as the title) would render chapterless sections numbered 0.x.
        body=body_tex,
        document_class_options=_class_options(options),
    )


def _report_base_level(body: str) -> int:
    """Heading shift mapping the shallowest `#`-level in `body` to `\\chapter`."""
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


def _str(options: Mapping[str, object], *keys: str) -> str | None:
    for key in keys:
        value = options.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _escaped(value: str | None) -> str | None:
    return escape_latex(value) if value is not None else None


def _derive_title(body: str) -> tuple[str | None, str]:
    """Pull the first ATX `#` heading out of `body` to use as the title.

    Returns the title (or `None` if there is no `#` heading) and the body with
    that heading line removed (so it does not also render as a chapter).
    """
    lines = body.splitlines()
    for index, line in enumerate(lines):
        match = _H1_RE.match(line)
        if match is not None:
            del lines[index]
            return match.group(1).strip(), "\n".join(lines)
    return None, body


def _class_options(options: Mapping[str, object]) -> set[PackageOption]:
    """Read class options from `classoptions` (list, dict, or comma string)."""
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
