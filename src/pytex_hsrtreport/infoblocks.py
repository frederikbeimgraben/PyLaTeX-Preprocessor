"""Coloured callout boxes, built from native pytex nodes.

The TeX-side ``ColoredBox`` environment is gone — :class:`ColoredBox` is a
:class:`pytex.TeX` node whose subtree is composed of :class:`Minipage`,
:class:`MDFramed`, :class:`Picture` / :class:`Put` and a sequence of
:class:`Command` nodes. The icon/background opacity is computed in Python
from the nesting depth, which we determine by walking the TeX tree at
construction time.

``InfoBox`` / ``WarningBox`` / ``SuccessBox`` / ``ImportantBox`` /
``DiscussionBox`` / ``CustomBox`` are thin wrappers that pick an icon + colour
pair. ``VotingResults`` runs the Ja/Nein/Enthaltung branching in Python and
builds the three sub-boxes inline as native :class:`Minipage` nodes.
"""

from dataclasses import dataclass, field
from typing import override

from pytex import (
    BuiltinPackages,
    Command,
    MDFramed,
    Minipage,
    Package,
    Picture,
    Put,
    TeX,
)
from pytex.model.raw import Raw, coerce_tex
from pytex_komascript.model import Block, Concat

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

    ``icon`` is the bare macro name (``"faInfoCircle"``, no leading backslash).
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
        icon: str = "faInfoCircle",
        icon_color: HSRTColor | str = "blue",
        background_color: HSRTColor | str | None = None,
        icon_size: str = "28pt",
        icon_offset_x: str = "0pt",
        icon_offset_y: str = "0pt",
    ) -> None:
        self.body = coerce_tex(body)
        self.icon = icon.lstrip("\\")
        self.icon_color = str(icon_color)
        self.background_color = str(
            background_color if background_color is not None else icon_color
        )
        self.icon_size = icon_size
        self.icon_offset_x = icon_offset_x
        self.icon_offset_y = icon_offset_y
        self._level = 1
        _bump_levels(self.body, self._level + 1)

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return set(_REQUIRES)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.body,)

    def set_level(self, level: int) -> None:
        """Re-tag the nesting level (used by :func:`_bump_levels`)."""
        self._level = level

    def _mdframed_options(self, bg_op: int) -> str:
        return (
            f"backgroundcolor={{{self.background_color}!{bg_op}}},"
            "hidealllines=true,"
            "skipabove=0.7\\baselineskip,skipbelow=0.7\\baselineskip,"
            "splitbottomskip=2pt,splittopskip=4pt,roundcorner=5pt"
        )

    def _icon_body(self, icon_op: int) -> TeX:
        return Block(
            Command("fontsize", self.icon_size, self.icon_size),
            Command("selectfont"),
            Command("color", f"{self.icon_color}!{icon_op}"),
            Command(self.icon),
        )

    def _tree(self) -> TeX:
        bg_op, icon_op = _opacity_pair(self._level)
        icon_put = Put(
            x=f"{self.icon_offset_x}-{self.icon_size}",
            y=f"{self.icon_offset_y}-0.7cm",
            body=self._icon_body(icon_op),
        )
        inner = Minipage(
            "\\linewidth-0.5cm",
            Command("vspace*", "0.5\\baselineskip"),
            self.body,
            Command("vspace*", "0.5\\baselineskip"),
        )
        framed = MDFramed(
            Picture(icon_put, width="\\linewidth", height="0", offset=("0", "0")),
            Command("hspace*", "0.25cm"),
            inner,
            options=self._mdframed_options(bg_op),
        )
        wrapper = Minipage("\\linewidth", framed)
        return Block(
            Command("vspace*", "0.5\\baselineskip"),
            Command("noindent"),
            wrapper,
        )

    @override
    def serialize(self) -> str:
        return self._tree().serialize()


def _bump_levels(node: TeX, level: int) -> None:
    """Recursively raise the level of every :class:`ColoredBox` under ``node``."""
    if isinstance(node, ColoredBox):
        node.set_level(level)
        _bump_levels(node.body, level + 1)
        return
    for child in node.children:
        _bump_levels(child, level)


# ---------------------------------------------------------------------------
# Preset callouts — pick icon + colour from a small palette.
# ---------------------------------------------------------------------------


def _body(parts: "tuple[TeX | str, ...]") -> TeX:
    from pytex import Group

    if len(parts) == 1:
        return coerce_tex(parts[0])
    return Group(*parts)


def InfoBox(*body: TeX | str, icon_size: str = "24pt") -> ColoredBox:
    """Blue info callout (``\\faInfoCircle``)."""
    return ColoredBox(
        _body(body),
        icon="faInfoCircle",
        icon_color="blue",
        icon_size=icon_size,
    )


def WarningBox(*body: TeX | str, icon_size: str = "24pt") -> ColoredBox:
    """Red warning callout (``\\faExclamationTriangle``)."""
    return ColoredBox(
        _body(body),
        icon="faExclamationTriangle",
        icon_color="red",
        icon_size=icon_size,
    )


def SuccessBox(*body: TeX | str, icon_size: str = "24pt") -> ColoredBox:
    """Green success callout (``\\faCheckCircle``)."""
    return ColoredBox(
        _body(body),
        icon="faCheckCircle",
        icon_color="green",
        icon_offset_y="2pt",
        icon_size=icon_size,
    )


def ImportantBox(*body: TeX | str, icon_size: str = "24pt") -> ColoredBox:
    """Orange important callout (``\\faExclamationCircle``)."""
    return ColoredBox(
        _body(body),
        icon="faExclamationCircle",
        icon_color="orange",
        icon_size=icon_size,
    )


def DiscussionBox(*body: TeX | str, icon_size: str = "24pt") -> ColoredBox:
    """Han-blue discussion callout (``\\faComments``)."""
    return ColoredBox(
        _body(body),
        icon="faComments",
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
    """ColoredBox with caller-chosen icon and accent colour.

    ``icon`` is the bare macro name (no leading backslash).
    """
    return ColoredBox(
        body,
        icon=icon,
        icon_color=color,
        icon_size=icon_size,
    )


def _tally(label: str, count: int, icon: str, hue: HSRTColor | str) -> TeX:
    """One Ja/Nein/Enthaltung sub-box wrapped in a 0.3-linewidth minipage.

    The label-and-count run is built with :class:`Concat` so the rendered
    body is ``\\textbf{label:} count`` without intervening whitespace; the
    ``Raw`` for the trailing count is a leaf-text escape hatch since plain
    numbers are not naturally a pytex node.
    """
    body = Concat(
        Command("textbf", f"{label}:"),
        Raw(f" {count}", escape_spaces=False),
    )
    return Minipage(
        "0.3\\linewidth", CustomBox(body, icon, hue), position="t"
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

    tally = Block(
        Command("par"),
        Command("medskip"),
        Command("noindent"),
        _tally("Ja", yes, "faThumbsUp", HSRTColor.BRITISH_RACING_GREEN),
        Command("hfill"),
        _tally("Nein", no, "faThumbsDown", "red"),
        Command("hfill"),
        _tally("Enthaltung", abstain, "faQuestion", HSRTColor.EGGPLANT),
    )
    return ColoredBox(
        Block(coerce_tex(body), tally),
        icon="faVoteYea",
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
