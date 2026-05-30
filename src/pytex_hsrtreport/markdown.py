"""Markdown -> TeX with HSRT callouts.

A variant of :func:`pytex.Markdown` that maps GitHub-style admonitions in
blockquotes (``> [!INFO]`` ...) to the HSRT InfoBlocks and fenced code blocks
with a language to per-language :class:`pytex.Listing` listings. Everything else
delegates to the core Markdown parser.
"""

import re

import marko
import marko.element
from marko import block, inline

from pytex import Listing, TeX
from pytex.library.markdown.parser import parse_md as _parse_core

from .infoblocks import (
    DiscussionBox,
    ImportantBox,
    InfoBox,
    SuccessBox,
    WarningBox,
)

_CALLOUT = re.compile(r"^\s*\[!([A-Za-z]+)\]\s*")

_CALLOUT_BOXES = {
    "INFO": InfoBox,
    "NOTE": InfoBox,
    "TIP": SuccessBox,
    "SUCCESS": SuccessBox,
    "WARNING": WarningBox,
    "CAUTION": WarningBox,
    "IMPORTANT": ImportantBox,
    "DISCUSSION": DiscussionBox,
}


def _first_rawtext(element: object) -> "inline.RawText | None":
    children: object = getattr(element, "children", None)
    if isinstance(children, str) or children is None:
        return None
    if not isinstance(children, (list, tuple)):
        return None
    for child in children:  # pyright: ignore[reportUnknownVariableType]
        child_obj: object = child
        if isinstance(child_obj, inline.RawText):
            return child_obj
        found = _first_rawtext(child_obj)
        if found is not None:
            return found
    return None


def _callout_kind(quote: "block.Quote") -> str | None:
    rawtext = _first_rawtext(quote)
    if rawtext is None:
        return None
    match = _CALLOUT.match(rawtext.children)
    if match is None:
        return None
    kind = match.group(1).upper()
    if kind not in _CALLOUT_BOXES:
        return None
    # Strip the marker in place so it is not rendered inside the box.
    rawtext.children = _CALLOUT.sub("", rawtext.children, count=1)
    return kind


def parse_md(element: marko.element.Element) -> TeX:
    """Parse a marko element, intercepting callouts and code fences."""
    if isinstance(element, block.Document):
        from pytex import Group

        return Group(*(parse_md(child) for child in element.children))

    if isinstance(element, block.Quote):
        kind = _callout_kind(element)
        if kind is not None:
            from pytex import Group

            body = Group(*(parse_md(child) for child in element.children))
            return _CALLOUT_BOXES[kind](body)

    if isinstance(element, (block.FencedCode, block.CodeBlock)):
        lang = getattr(element, "lang", "") or None
        code = ""
        if element.children:
            code = "".join(
                child.children if isinstance(child, inline.RawText) else str(child)
                for child in element.children
            )
        if lang:
            return Listing(code, language=lang)

    return _parse_core(element)


def markdown_to_tex(markdown_text: str) -> TeX:
    """Convert Markdown text to TeX using HSRT callouts and listings."""
    return parse_md(marko.parse(markdown_text))


Markdown = markdown_to_tex
