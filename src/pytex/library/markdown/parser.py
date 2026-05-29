# pyright:  reportAny=false
from typing import TYPE_CHECKING

import marko
import marko.element
from marko import block, inline

if TYPE_CHECKING:
    pass

from ..builtins.text_and_sections import (
    Bold,
    Href,
    Italic,
    Newline,
    Paragraph,
    Section,
    Subparagraph,
    Subsection,
    Subsubsection,
    Texttt,
)
from ..environments.standard import Enumerate, Item, Itemize, Quote, Verbatim
from ...model.base_model import TeX
from ...model.group import Group
from ...model.raw import Raw


def parse_md(element: marko.element.Element) -> TeX:
    """Parse a marko Element into a TeX object"""

    # Block elements
    if isinstance(element, block.Document):
        return Group(*(parse_md(child) for child in element.children))

    if isinstance(element, block.Paragraph):
        # Parse inline body
        if hasattr(element, "children") and element.children:
            return Paragraph(Group(*(parse_md(child) for child in element.children)))
        return Raw("")

    if isinstance(element, block.Heading):
        heading_content = Group(*(parse_md(child) for child in element.children))
        level = element.level

        if level == 1:
            return Section(heading_content)
        elif level == 2:
            return Subsection(heading_content)
        elif level == 3:
            return Subsubsection(heading_content)
        elif level == 4:
            return Paragraph(heading_content)
        else:  # level 5 or 6
            return Subparagraph(heading_content)

    if isinstance(element, (block.FencedCode, block.CodeBlock)):
        # Extract code text from RawText children
        if element.children:
            code_text = "".join(
                child.children if isinstance(child, inline.RawText) else str(child)
                for child in element.children
            )
            return Verbatim(code_text)
        return Verbatim("")

    if isinstance(element, block.Quote):
        return Quote(Group(*(parse_md(child) for child in element.children)))

    if isinstance(element, block.List):
        items = [Item(parse_md(child)) for child in element.children]
        if element.ordered:
            return Enumerate(*items)
        else:
            return Itemize(*items)

    if isinstance(element, block.ListItem):
        return Group(*(parse_md(child) for child in element.children))

    if isinstance(element, block.ThematicBreak):
        # Horizontal rule - use a simple line
        return Raw("\\hrule")

    if isinstance(element, block.HTMLBlock):
        # Raw HTML - just output as-is (or skip)
        return Raw(element.body if hasattr(element, "body") else "")

    if isinstance(element, block.BlankLine):
        return Raw("\n")

    # Inline elements
    if isinstance(element, inline.RawText):
        # Escape special LaTeX characters
        text = element.children
        # Basic escaping for common LaTeX special chars
        replacements = {
            "\\": r"\textbackslash{}",
            "{": r"\{",
            "}": r"\}",
            "$": r"\$",
            "&": r"\&",
            "%": r"\%",
            "#": r"\#",
            "_": r"\_",
            "~": r"\textasciitilde{}",
            "^": r"\textasciicircum{}",
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return Raw(text, safe=False)

    if isinstance(element, inline.Emphasis):
        children = element.children
        if not isinstance(children, str):
            return Italic(Group(*(parse_md(child) for child in children)))
        return Raw(children, safe=False)

    if isinstance(element, inline.StrongEmphasis):
        children = element.children
        if not isinstance(children, str):
            return Bold(Group(*(parse_md(child) for child in children)))
        return Raw(children, safe=False)

    if isinstance(element, inline.CodeSpan):
        return Texttt(Raw(element.children, safe=False))

    if isinstance(element, inline.Link):
        children = element.children
        if not isinstance(children, str):
            link_text = Group(*(parse_md(child) for child in children))
        else:
            link_text = Raw(children, safe=False)
        link_url = Raw(element.dest, safe=False)
        return Href(link_url, link_text)

    if isinstance(element, inline.Image):
        # Images would need graphicx package - simplified here
        return Raw(f"[Image: {element.dest}]", safe=False)

    if isinstance(element, inline.AutoLink):
        url = element.dest
        return Href(Raw(url, safe=False), Raw(url, safe=False))

    if isinstance(element, inline.LineBreak):
        if hasattr(element, "soft") and element.soft:
            return Raw(" ")
        else:
            return Newline

    if isinstance(element, inline.Literal):
        return Raw(element.children, safe=False)

    if isinstance(element, inline.InlineHTML):
        # Raw inline HTML - just output as-is (or skip)
        return Raw(element.children if element.children else "", safe=False)

    # Fallback for unknown elements
    if hasattr(element, "children"):
        children = getattr(element, "children")
        if isinstance(children, str):
            return Raw(children, safe=False)
        elif hasattr(children, "__iter__"):
            return Group(*(parse_md(child) for child in children))

    return Raw("")


def markdown_to_tex(markdown_text: str) -> TeX:
    """Convert Markdown text to a TeX object.

    Args:
        markdown_text: Markdown formatted text string

    Returns:
        TeX object representing the parsed markdown

    Example:
        >>> tex = markdown_to_tex("# Hello\\n\\nThis is **bold**")
        >>> print(tex.serialize())
    """
    doc = marko.parse(markdown_text)
    return parse_md(doc)


# Alias for backwards compatibility
Markdown = markdown_to_tex
