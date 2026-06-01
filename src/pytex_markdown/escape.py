"""Escape literal text for LaTeX.

Markdown text is plain prose, so every LaTeX-special character must be escaped
before it reaches the document. pytex itself does no escaping (strings pass
through as ``Raw``), so this lives here.
"""

from __future__ import annotations

from typing import Final

# Order matters only in that backslash maps to a command; we build the result
# char-by-char so the braces introduced by replacements are never re-escaped.
_ESCAPES: Final[dict[str, str]] = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def escape_latex(text: str) -> str:
    """Return ``text`` with LaTeX-special characters escaped."""
    return "".join(_ESCAPES.get(ch, ch) for ch in text)
