"""Markdown -> native PyTeX conversion.

Exposes two registered factories:

* ``Markdown(content, ...)``        - convert a Markdown string to a ``TeX`` tree.
* ``IncludeMarkdown(path, ...)``    - read a file and convert it.

GitHub-style callouts (``> [!NOTE]`` ...) become HSRT ``ColoredBox`` presets,
so this package depends on ``pytex_hsrtreport``.
"""

from __future__ import annotations

from os import PathLike
from pathlib import Path

import marko

from pytex.interface.tex import TeX
from pytex.registry import Registry

from .convert import MarkdownConverter
from .escape import escape_latex

__all__ = ["Markdown", "IncludeMarkdown", "MarkdownConverter", "escape_latex"]

_PARSER = marko.Markdown()


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
    ast = _PARSER.parse(content)
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
