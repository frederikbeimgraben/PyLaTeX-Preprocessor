"""Coloured callout boxes, fully native.

The TeX-side ``ColoredBox`` environment is gone — :class:`ColoredBox` is a
:class:`pytex.TeX` node that emits the boxed-and-decorated body inline, with
the icon/background opacity computed in Python from the nesting depth (which
we determine by walking the TeX tree at construction time).

``InfoBox`` / ``WarningBox`` / ``SuccessBox`` / ``ImportantBox`` /
``DiscussionBox`` / ``CustomBox`` are thin wrappers that pick an icon + colour
pair. ``VotingResults`` runs the Ja/Nein/Enthaltung branching in Python and
builds the three sub-boxes inline.
"""

from dataclasses import dataclass, field
from typing import override

from pytex import BuiltinPackages, Group, Package, TeX
from pytex.model.raw import Raw, coerce_tex

from .colors import HSRTColor

_REQUIRES: frozenset[Package | str] = frozenset(
    {
        BuiltinPackages.MDFRAMED.value,
        BuiltinPackages.FONTAWESOME5.value,
        BuiltinPackages.MULTICOL.value,
    }
)


def _opacity_pair(level: int) -> tuple[int, int]:
    """``(background, icon)`` opacity percents for a given nesting level.

    Mirrors the original ``\\FPeval`` formulas: bg = round((0.05 + 0.075 · L) ·
    100); icon = bg + 20. With L=1 we get (12, 32) — same numbers the .cls
    would compute on its own.
    """
    background = round((0.05 + 0.075 * level) * 100)
    return background, background + 20


@dataclass(init=False)
class ColoredBox(TeX):
    """A boxed callout with icon and tinted background.

    All decoration parameters live in Python. The body is rendered inline; no
    ``\\begin{ColoredBox}`` environment exists in TeX. When a :class:`ColoredBox`
    is nested inside another, the inner instance's ``_level`` is bumped at
    construction time so its background tint deepens.
    """

    body: TeX
    icon: str
    icon_color: str
    background_color: str
    icon_size: str = "28pt"
    icon_offset_x: str = "0pt"
    icon_offset_y: str = "0pt"
    _level: int = field(default=1)

    def __init__(
        self,
        body: TeX | str,
        *,
        icon: str = "\\faInfoCircle",
        icon_color: HSRTColor | str = "blue",
        background_color: HSRTColor | str | None = None,
        icon_size: str = "28pt",
        icon_offset_x: str = "0pt",
        icon_offset_y: str = "0pt",
    ) -> None:
        self.body = coerce_tex(body)
        self.icon = icon
        self.icon_color = str(icon_color)
        self.background_color = str(
            background_color if background_color is not None else icon_color
        )
        self.icon_size = icon_size
        self.icon_offset_x = icon_offset_x
        self.icon_offset_y = icon_offset_y
        self._level = 1
        # Bump nested ColoredBoxes one notch deeper than this one.
        _bump_levels(self.body, self._level + 1)

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return set(_REQUIRES)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.body,)

    @override
    def serialize(self) -> str:
        bg_op, icon_op = _opacity_pair(self._level)
        return (
            "\\vspace*{0.5\\baselineskip}\\noindent\n"
            "\\begin{minipage}{\\linewidth}\n"
            "\\begin{mdframed}["
            f"backgroundcolor={{{self.background_color}!{bg_op}}},"
            "hidealllines=true,"
            "skipabove=0.7\\baselineskip,skipbelow=0.7\\baselineskip,"
            "splitbottomskip=2pt,splittopskip=4pt,roundcorner=5pt]\n"
            "\\begin{picture}(\\linewidth, 0)(0, 0)\n"
            f"\\put({self.icon_offset_x}-{self.icon_size},"
            f"{self.icon_offset_y}-0.7cm){{"
            f"\\fontsize{{{self.icon_size}}}{{{self.icon_size}}}\\selectfont "
            f"\\color{{{self.icon_color}!{icon_op}}} {self.icon}}}\n"
            "\\end{picture}\\hspace*{0.25cm}\n"
            "\\begin{minipage}{\\linewidth-0.5cm}\n"
            f"\\vspace*{{0.5\\baselineskip}}{self.body.serialize()}"
            "\\vspace*{0.5\\baselineskip}\n"
            "\\end{minipage}\n"
            "\\end{mdframed}\n"
            "\\end{minipage}"
        )


def _bump_levels(node: TeX, level: int) -> None:
    """Recursively raise the ``_level`` of every :class:`ColoredBox` under ``node``."""
    if isinstance(node, ColoredBox):
        # Note: assignment is OK — ColoredBox is not frozen.
        node._level = level
        _bump_levels(node.body, level + 1)
        return
    for child in node.children:
        _bump_levels(child, level)


# ---------------------------------------------------------------------------
# Preset callouts — pick icon + colour from a small palette.
# ---------------------------------------------------------------------------


def _body(parts: "tuple[TeX | str, ...]") -> TeX:
    if len(parts) == 1:
        return coerce_tex(parts[0])
    return Group(*parts)


def InfoBox(*body: TeX | str, icon_size: str = "24pt") -> ColoredBox:
    """Blue info callout (``\\faInfoCircle``)."""
    return ColoredBox(
        _body(body),
        icon="\\faInfoCircle",
        icon_color="blue",
        icon_size=icon_size,
    )


def WarningBox(*body: TeX | str, icon_size: str = "24pt") -> ColoredBox:
    """Red warning callout (``\\faExclamationTriangle``)."""
    return ColoredBox(
        _body(body),
        icon="\\faExclamationTriangle",
        icon_color="red",
        icon_size=icon_size,
    )


def SuccessBox(*body: TeX | str, icon_size: str = "24pt") -> ColoredBox:
    """Green success callout (``\\faCheckCircle``)."""
    return ColoredBox(
        _body(body),
        icon="\\faCheckCircle",
        icon_color="green",
        icon_offset_y="2pt",
        icon_size=icon_size,
    )


def ImportantBox(*body: TeX | str, icon_size: str = "24pt") -> ColoredBox:
    """Orange important callout (``\\faExclamationCircle``)."""
    return ColoredBox(
        _body(body),
        icon="\\faExclamationCircle",
        icon_color="orange",
        icon_size=icon_size,
    )


def DiscussionBox(*body: TeX | str, icon_size: str = "24pt") -> ColoredBox:
    """Han-blue discussion callout (``\\faComments``)."""
    return ColoredBox(
        _body(body),
        icon="\\faComments",
        icon_color=HSRTColor.HANBLUE,
        icon_size=icon_size,
    )


def CustomBox(
    body: TeX | str,
    icon: str,
    color: HSRTColor | str,
    *,
    icon_size: str = "24pt",
) -> ColoredBox:
    """ColoredBox with caller-chosen icon and accent colour."""
    return ColoredBox(
        body,
        icon=icon,
        icon_color=color,
        icon_size=icon_size,
    )


def VotingResults(
    body: TeX | str,
    yes: int,
    no: int,
    abstain: int,
) -> ColoredBox:
    """ColoredBox with a vote-tally trailer (Ja/Nein/Enthaltung).

    The accent colour reflects the outcome (green/red/eggplant), chosen in
    Python instead of via ``\\ifnum`` inside a ``\\NewEnviron``.
    """
    color: HSRTColor | str
    if yes > no:
        color = HSRTColor.BRITISH_RACING_GREEN
    elif yes < no:
        color = "red"  # built-in xcolor name; no HSRT entry needed
    else:
        color = HSRTColor.EGGPLANT

    def _tally(label: str, count: int, icon: str, hue: HSRTColor | str) -> str:
        inner = CustomBox(
            Raw(f"\\textbf{{{label}:}} {count}", escape_spaces=False),
            icon,
            hue,
        )
        return (
            f"\\begin{{minipage}}[t]{{0.3\\linewidth}}"
            f"{inner.serialize()}"
            f"\\end{{minipage}}"
        )

    tally = (
        "\\par\\medskip\\noindent\n"
        f"{_tally('Ja', yes, '\\faThumbsUp', HSRTColor.BRITISH_RACING_GREEN)}"
        "\\hfill\n"
        f"{_tally('Nein', no, '\\faThumbsDown', 'red')}"
        "\\hfill\n"
        f"{_tally('Enthaltung', abstain, '\\faQuestion', HSRTColor.EGGPLANT)}"
    )
    return ColoredBox(
        Group(coerce_tex(body), Raw(tally, escape_spaces=False)),
        icon="\\faVoteYea",
        icon_color=color,
        icon_offset_x="-0.2cm",
        icon_size="24pt",
    )


__all__ = [
    "ColoredBox",
    "InfoBox",
    "WarningBox",
    "SuccessBox",
    "ImportantBox",
    "DiscussionBox",
    "CustomBox",
    "VotingResults",
]
