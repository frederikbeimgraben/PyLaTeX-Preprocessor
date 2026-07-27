"""Sanitize text from a source you do not trust before it enters a document.

`Sanitize` handles two independent concerns, and each one has its own flag.

1. When `tex` is True, `Sanitize` escapes the LaTeX-special characters, so
   the text renders literally. PyTeX escapes nothing by itself, and a `Raw`
   node passes its text straight through.
2. When `pytex` is True, `Sanitize` stops PyTeX from evaluating an inline
   `pytex(...)` marker in the content. The marker can run any Python code, so
   this matters for content from outside the program.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from ..model.raw import Raw
from ..registry import Registry

__all__ = ["Sanitize", "escape_latex"]

if TYPE_CHECKING:
    from ..interface.tex import TeX

# `escape_latex` reads the text one character at a time, so it never escapes
# a brace that a replacement adds.
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
    # PyTeX always loads babel with `ngerman`, which makes `"` an active
    # shorthand character. LaTeX would swallow or mangle a literal double
    # quote. `\textquotedbl{}` is a font-encoding macro (T1 or textcomp) and
    # not a shorthand, so it prints an upright double quote without a change.
    # The empty group stops LaTeX from eating the space after the macro.
    '"': r"\textquotedbl{}",
}


def escape_latex(text: str) -> str:
    """Return `text` with the LaTeX-special characters escaped.

    The function replaces every character that `ESCAPES` names. It leaves
    every other character unchanged.
    """
    return "".join(ESCAPES.get(ch, ch) for ch in text)


@Registry.add
def Sanitize(content: str, pytex: bool = True, tex: bool = True) -> TeX:
    """Wrap `content` in a `Raw` node and make unsafe input harmless.

    Args:
        pytex: True stops PyTeX from evaluating an inline `pytex(...)` marker
            in the content. Default True.
        tex: True escapes the LaTeX-special characters in the content.
            Default True.

    Returns:
        A `Raw` node that holds the sanitized text.
    """
    text = escape_latex(content) if tex else content
    return Raw(text, allow_replacements=not pytex)
