"""Sanitize untrusted text before it enters a document.

Two independent concerns:

* ``tex``   - escape LaTeX-special characters so the text renders literally
  (pytex itself does no escaping; raw strings pass straight through).
* ``pytex`` - disable PyTeX replacement so an embedded
  ``\\iffalse{pytex(...)}\\fi`` marker is never evaluated. The marker can run
  arbitrary Python, so this matters for content from outside the program.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from ..model.raw import Raw
from ..registry import Registry

__all__ = ["Sanitize", "escape_latex"]

if TYPE_CHECKING:
    from ..interface.tex import TeX

# Build the result char-by-char so braces introduced by a replacement are
# never themselves re-escaped.
ESCAPES: Final[dict[str, str]] = {
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
    # babel ngerman (always loaded) makes `"` an active shorthand char, so a
    # literal double quote would be swallowed/mangled. `\textquotedbl{}` is a
    # font-encoding macro (T1/textcomp), not a shorthand, so it prints an
    # upright double quote untouched; the empty group stops space-gobbling.
    '"': r"\textquotedbl{}",
}


def escape_latex(text: str) -> str:
    """Return ``text`` with LaTeX-special characters escaped."""
    return "".join(ESCAPES.get(ch, ch) for ch in text)


@Registry.add
def Sanitize(content: str, pytex: bool = True, tex: bool = True) -> TeX:
    """Wrap ``content`` as a ``TeX`` node, neutralising unsafe input.

    * ``tex=True``   escapes LaTeX-special characters.
    * ``pytex=True`` prevents any ``\\iffalse{pytex(...)}\\fi`` marker in the
      content from being evaluated.
    """
    text = escape_latex(content) if tex else content
    return Raw(text, allow_replacements=not pytex)
