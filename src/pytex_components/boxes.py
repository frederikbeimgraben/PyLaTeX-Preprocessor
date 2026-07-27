from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Final, override

from pytex.commands.builtin import HspaceStar, Noindent, VspaceStar
from pytex.commands.colors import SelectColor
from pytex.commands.floats import Minipage
from pytex.commands.font import Fontsize, Selectfont
from pytex.commands.fontawesome import FaIcon
from pytex.commands.mdframed import Mdframed
from pytex.commands.picture import Picture, Put
from pytex.helpers.parenting import attach
from pytex.interface.package import PackageProtocol
from pytex.interface.tex import TeX
from pytex.model.concat import Concat
from pytex.model.raw import Raw
from pytex.packages import CALC, FONTAWESOME, MDFRAMED, TIKZ, XCOLOR
from pytex.registry import Registry

__all__ = [
    "ColoredBox",
    "CustomBox",
    "DiscussionBox",
    "ImportantBox",
    "InfoBox",
    "SuccessBox",
    "WarningBox",
]

BASE_OPACITY: Final[float] = 0.05
PER_LEVEL: Final[float] = 0.075
ICON_BOOST: Final[int] = 20

# The nesting depth at render time. It mirrors the LaTeX `coloredBoxLevel`
# counter. The depth starts at 0, grows by 1 for each nesting level, and
# returns to the old value on exit.
#
# This is a `ContextVar` and not a plain module global. Two renders that run
# at the same time must not overwrite each other's depth. Each OS thread
# starts from the `default`, and each `asyncio` task gets its own copy of the
# context.
#
# A plain module-level `int` is shared mutable state. Under threaded or async
# rendering the nested boxes of one render bump the counter that another
# render reads. The other render then gets the wrong opacity, and nothing
# reports the error. Single-threaded behavior is the same either way.
#
# For more detail read `docs/render-depth-and-api-module.md`.
_render_depth: ContextVar[int] = ContextVar("coloredbox_render_depth", default=0)


@Registry.add
@dataclass(frozen=True)
class ColoredBox(TeX):
    """A colored box whose background opacity grows with the nesting depth.

    The box matches the LaTeX `ColoredBox` environment from HSRTReport. PyTeX
    resolves the depth counter `coloredBoxLevel` in Python at render time. It
    does not use a global LaTeX counter.

    Attributes:
        icon_size: A LaTeX length, for example `28pt`. It sets both the font
            size and the baseline skip of the icon.
        icon_offset_x: A LaTeX length that moves the icon to the right.
        icon_offset_y: A LaTeX length that moves the icon up.
        icon_color: An xcolor color name, for example `blue`.
        background_color: An xcolor color name, for example `blue`.
    """

    body: Final[TeX | str]
    icon: Final[TeX | str] = field(default_factory=lambda: FaIcon("info-circle"))
    icon_color: Final[str] = "blue"
    icon_size: Final[str] = "28pt"
    icon_offset_x: Final[str] = "0pt"
    icon_offset_y: Final[str] = "0pt"
    background_color: Final[str] = "blue"
    _parent: "TeX | None" = field(default=None, init=False, compare=False, repr=False)

    def __post_init__(self) -> None:
        attach(self, self.body, self.icon)

    @property
    def nesting_level(self) -> int:
        """The depth of this box in the parent chain, counted from 1.

        The value is 1 for the outermost box and 2 for a box inside one other
        box. The count uses the parent chain, so a box that PyTeX renders in
        isolation always reports 1.
        """
        return 1 + sum(1 for p in self.parents if isinstance(p, ColoredBox))

    @property
    def background_opacity(self) -> int:
        """The background opacity in percent, from the parent-chain depth.

        `rendered` reads the render-time depth counter instead. The two values
        differ for a box that PyTeX builds inside the `rendered` property of
        another node, because that build breaks the parent chain.
        """
        return round((BASE_OPACITY + PER_LEVEL * self.nesting_level) * 100)

    @property
    def icon_opacity(self) -> int:
        """The icon opacity in percent, which is `background_opacity` plus 20."""
        return self.background_opacity + ICON_BOOST

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return tuple(v for v in (self.body, self.icon) if isinstance(v, TeX))

    @property
    @override
    def requires(self) -> frozenset[PackageProtocol]:
        # The box requires `calc`, because it uses infix length arithmetic
        # such as `\linewidth-0.5cm` and `\put(x-size,...)`. That arithmetic
        # is valid only with `calc`.
        # The box requires `tikz`, because `tikz` is the mdframed framemethod
        # that rounds the filled background when the frame lines are hidden.
        return frozenset({MDFRAMED, XCOLOR, FONTAWESOME, CALC, TIKZ})

    @property
    @override
    def rendered(self) -> str:
        # This is a faithful port of the HSRTReport `ColoredBox` environment.
        # A picture of zero height puts the icon over the top-left corner, and
        # the body sits in a narrower minipage next to it. The infix length
        # arithmetic needs `calc`. See `requires`.
        #
        # The counter below tracks the nesting depth at render time. It
        # mirrors the LaTeX `coloredBoxLevel`. The parent chain cannot do this
        # job here, because the wrapper nodes below attach the body again and
        # break that chain before the inner box renders.
        depth = _render_depth.get() + 1
        token = _render_depth.set(depth)
        try:
            # Prefer the render counter. It is correct for top-down
            # rendering, where the wrappers break the parent chain. Fall back
            # to the parent chain, so that a box which PyTeX renders in
            # isolation still gets the right depth.
            level = max(depth, self.nesting_level)
            bg = round((BASE_OPACITY + PER_LEVEL * level) * 100)
            icon_op = bg + ICON_BOOST
            return Concat(
                VspaceStar(r"0.5\baselineskip"),
                Raw("~\\\\"),
                Noindent(),
                Minipage(
                    r"\linewidth",
                    Mdframed(
                        Concat(
                            # An overlay of zero size. LaTeX draws the icon at
                            # the `\put` coordinates and reserves no width for
                            # it, so the body minipage flows as normal and
                            # does not overflow.
                            Picture(
                                "0",
                                "0",
                                Put(
                                    f"{self.icon_offset_x}+0.2cm-{self.icon_size}",
                                    self.icon_offset_y,
                                    # `\vcenter` centers the real bounding box
                                    # of each glyph on the math axis. Circles,
                                    # triangles and ticks then line up with
                                    # the first text line, whatever their font
                                    # metrics are.
                                    Concat(
                                        Raw(r"$\vcenter{\hbox{"),
                                        Fontsize(self.icon_size, self.icon_size),
                                        Selectfont(),
                                        SelectColor(f"{self.icon_color}!{icon_op}"),
                                        self.icon,
                                        Raw(r"}}$"),
                                    ),
                                ),
                            ),
                            HspaceStar("0.25cm+2pt"),
                            Minipage(
                                r"\linewidth-0.5cm-2pt",
                                self.body,
                                align="t",
                            ),
                        ),
                        options={
                            "backgroundcolor": f"{self.background_color}!{bg}",
                            "hidealllines": "true",
                            "skipabove": r"0.7\baselineskip",
                            "skipbelow": r"0.7\baselineskip",
                            "innertopmargin": "0.45cm",
                            "innerbottommargin": "0.45cm",
                            "splitbottomskip": "2pt",
                            "splittopskip": "4pt",
                            "roundcorner": "5pt",
                        },
                    ),
                ),
            ).rendered
        finally:
            _render_depth.reset(token)


def _preset(
    body: TeX | str,
    icon_name: str | None,
    color: str,
    icon_size: str = "24pt",
    icon_offset_x: str = "1.5pt",
    icon_offset_y: str = "0pt",
) -> ColoredBox:
    return ColoredBox(
        body=body,
        icon=FaIcon(icon_name),
        icon_color=color,
        icon_size=icon_size,
        icon_offset_x=icon_offset_x,
        icon_offset_y=icon_offset_y,
        background_color=color,
    )


@Registry.add
def InfoBox(body: TeX | str) -> ColoredBox:
    """Return a blue `ColoredBox` with the `info-circle` icon."""
    return _preset(body, "info-circle", "blue", icon_offset_y="2pt")


@Registry.add
def WarningBox(body: TeX | str) -> ColoredBox:
    """Return a red `ColoredBox` with the `exclamation-triangle` icon."""
    return _preset(
        body, "exclamation-triangle", "red", icon_offset_y="1pt", icon_offset_x="0.5pt"
    )


@Registry.add
def SuccessBox(body: TeX | str) -> ColoredBox:
    """Return a green `ColoredBox` with the `check-circle` icon."""
    return _preset(body, "check-circle", "green")


@Registry.add
def ImportantBox(body: TeX | str) -> ColoredBox:
    """Return an orange `ColoredBox` with the `exclamation-circle` icon."""
    return _preset(
        body,
        "exclamation-circle",
        "orange",
    )


@Registry.add
def CustomBox(body: TeX | str, icon: str | None, color: str) -> ColoredBox:
    """Return a `ColoredBox` with a free choice of icon and color.

    Args:
        icon: A fontawesome version 4 icon name, for example `check-circle`.
            None gives a box with no icon.
        color: An xcolor color name. The document must define the name.
    """
    return _preset(body, icon, color)


@Registry.add
def DiscussionBox(body: TeX | str) -> ColoredBox:
    """Return a `ColoredBox` in `hanblue` with the `comments` icon.

    Only `pytex_hsrtreport.colors` defines `hanblue`. A document without that
    color definition fails to compile.
    """
    return _preset(body, "comments", "hanblue")
