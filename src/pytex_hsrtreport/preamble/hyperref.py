"""``\\hypersetup{...}`` configuration block."""

from pytex import Hypersetup, TeX

_HYPERSETUP_OPTIONS: tuple[str, ...] = (
    "pdfpagemode={UseOutlines}",
    "bookmarksopen=true",
    "bookmarksopenlevel=0",
    "hypertexnames=false",
    "colorlinks=true",
    "citecolor=[rgb]{0.286, 0.427, 0.537}",
    "linkcolor=[rgb]{0.161, 0.31, 0.427}",
    "urlcolor=[rgb]{0.071, 0.212, 0.322}",
    "pdfstartview={FitV}",
    "unicode",
    "breaklinks=true",
)


def HyperrefBlock() -> TeX:
    return Hypersetup(",".join(_HYPERSETUP_OPTIONS))


__all__ = ["HyperrefBlock"]
