"""Markdown -> native PyTeX conversion.

Exposes two registered factories:

* ``Markdown(content, ...)``        - convert a Markdown string to a ``TeX`` tree.
* ``IncludeMarkdown(path, ...)``    - read a file and convert it.

GitHub-style callouts (``> [!NOTE]`` ...) become HSRT ``ColoredBox`` presets,
so this package depends on ``pytex_hsrtreport``.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import marko

from pytex.registry import Registry

from .convert import MarkdownConverter
from .escape import escape_latex

if TYPE_CHECKING:
    from os import PathLike

    from pytex.interface.tex import TeX

__all__ = ["IncludeMarkdown", "Markdown", "MarkdownConverter", "escape_latex"]

# GFM enables pipe tables (and strikethrough/autolinks); images are core.
PARSER = marko.Markdown(extensions=["gfm"])


@Registry.add
def Markdown(
    content: str,
    *,
    base_level: int = 0,
    callouts: bool = True,
) -> TeX:
    """Convert a Markdown string to a ``TeX`` tree.

    ``base_level`` shifts heading depth: ``0`` maps ``#`` to ``\\section`` (the
    default), ``-1`` maps it to ``\\chapter``. ``callouts`` toggles converting
    ``> [!NOTE]`` blocks into HSRT colored boxes.
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
    """Read a Markdown file and convert it (see :func:`Markdown`)."""
    content = Path(path).read_text(encoding=encoding)
    return Markdown(content, base_level=base_level, callouts=callouts)
