"""Markdown conversion into TeX nodes.

The Markdown converter registers two factories:

* `Markdown(content, ...)` converts a Markdown string to a node tree.
* `IncludeMarkdown(path, ...)` reads a file and converts it.

A GitHub-style callout (`> [!NOTE]` and the other markers) becomes a
`pytex_components` colored box, so this package needs `pytex_components`.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import marko

from pytex.registry import Registry

from .convert import MarkdownConverter
from .escape import escape_latex
from .frontmatter import FrontmatterValue, split_frontmatter

if TYPE_CHECKING:
    from os import PathLike

    from pytex.interface.tex import TeX

__all__ = [
    "FrontmatterValue",
    "IncludeMarkdown",
    "Markdown",
    "MarkdownConverter",
    "escape_latex",
    "split_frontmatter",
]

# The `gfm` extension adds pipe tables, strikethrough and autolinks. Images
# need no extension, because core Markdown already has them.
PARSER = marko.Markdown(extensions=["gfm"])


@Registry.add
def Markdown(
    content: str,
    *,
    base_level: int = 0,
    callouts: bool = True,
) -> TeX:
    """Convert a Markdown string to a node tree.

    Args:
        base_level: The shift applied to the heading depth. The default `0`
            maps a Markdown `#` to `\\section`. A value of `-1` maps it to
            `\\chapter`.
        callouts: When true, a `> [!NOTE]` block becomes a colored box. When
            false, the block stays an ordinary quote.
    """
    ast = PARSER.parse(content)
    converter = MarkdownConverter(base_level=base_level, callouts=callouts)
    return converter.block(ast)


@Registry.add
def IncludeMarkdown(
    path: str | PathLike[str],
    *,
    base_level: int = 0,
    callouts: bool = True,
    encoding: str = "utf-8",
) -> TeX:
    """Read a Markdown file and convert it.

    The `base_level` and `callouts` arguments have the same meaning as in
    `Markdown`.

    Args:
        encoding: The text encoding of the file. The default is `utf-8`.
    """
    content = Path(path).read_text(encoding=encoding)
    return Markdown(content, base_level=base_level, callouts=callouts)
