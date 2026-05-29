"""Page watermark — supplies ``\\waterMarkText`` from Python and includes the
diagonal-text :file:`tex/watermark.tex` definition.
"""

from pathlib import Path

from pytex import IncludeTeX, NewCommand, TeX
from pytex_komascript.model import Block

_TEX_DIR = Path(__file__).parent / "tex"


def watermark_block(text: str = "") -> TeX:
    """``\\newcommand{\\waterMarkText}{text}`` + watermark draftwatermark setup."""
    return Block(
        NewCommand("waterMarkText", text),
        IncludeTeX(_TEX_DIR / "watermark.tex"),
    )
