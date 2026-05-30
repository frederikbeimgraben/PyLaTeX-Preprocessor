"""Page-break penalties, length declarations and the hooks in ``pagebreaks.tex``."""

from pytex import (
    IncludeTeX,
    NewCommand,
    NewLength,
    SetLength,
    TeX,
)
from pytex_komascript.model import Block

from ..paths import TEX_DIR


def pagebreaks_block() -> TeX:
    return Block(
        NewLength("sectionminspace"),
        NewLength("subsectionminspace"),
        NewLength("subsubsectionminspace"),
        SetLength("sectionminspace", "12\\baselineskip"),
        SetLength("subsectionminspace", "10\\baselineskip"),
        SetLength("subsubsectionminspace", "8\\baselineskip"),
        NewCommand(
            "keeptogether",
            "\\begin{minipage}{\\linewidth}#1\\end{minipage}",
            n_args=1,
        ),
        NewCommand(
            "protectparagraph",
            "\\nopagebreak[4]\\interlinepenalty=10000",
        ),
        NewCommand(
            "conditionalpagebreak",
            "\\needspace{#1}",
            n_args=1,
            default="10\\baselineskip",
        ),
        IncludeTeX(TEX_DIR / "pagebreaks.tex"),
    )


__all__ = ["pagebreaks_block"]
