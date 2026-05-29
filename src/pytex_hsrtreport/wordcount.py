"""Pure-Python word counting over a TeX tree.

Walks the document tree, gathers the text held in leaf nodes, strips LaTeX
layout (control sequences, braces, math, comments, alignment), and counts the
remaining prose tokens. This replaces the shell ``texcount`` dependency of the
original class.
"""

import re

from pytex import TeX
from pytex.model.raw import Raw

_COMMENT = re.compile(r"(?<!\\)%.*")
_CONTROL_SEQ = re.compile(r"\\[a-zA-Z@]+\*?|\\.")
_MATH = re.compile(r"\$[^$]*\$")
_MARKUP = re.compile(r"[{}\[\]&#~^_]")
_WS = re.compile(r"\s+")


def _gather_text(node: TeX, parts: list[str]) -> None:
    if isinstance(node, Raw):
        parts.append(str(node.content))
    for child in node.children:
        _gather_text(child, parts)


def strip_latex(text: str) -> str:
    """Remove LaTeX layout, leaving only prose."""
    text = _COMMENT.sub("", text)
    text = _MATH.sub(" ", text)
    text = _CONTROL_SEQ.sub(" ", text)
    text = _MARKUP.sub(" ", text)
    return _WS.sub(" ", text).strip()


def content_text(node: TeX) -> str:
    """All prose text in the tree, layout stripped."""
    parts: list[str] = []
    _gather_text(node, parts)
    return strip_latex(" ".join(parts))


def count_words(node: TeX) -> int:
    """Number of prose words in the tree."""
    text = content_text(node)
    return len(text.split()) if text else 0
