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

# Render-time nesting depth, mirroring LaTeX's `coloredBoxLevel` counter.
#
# A `ContextVar` rather than a plain module global so concurrent renders do not
# clobber each other's depth: each OS thread starts from the `default` and each
# `asyncio` task inherits an independent copy of the context. A bare `int +=`
# here is shared mutable state — under threaded/async rendering one render's
# nested boxes bump the counter that a sibling render reads, silently producing
# wrong opacities. Single-threaded behaviour is identical (default 0, +1 per
# nesting level, restored on exit). See docs/render-depth-and-api-module.md.
_render_depth: ContextVar[int] = ContextVar("coloredbox_render_depth", default=0)


@Registry.add
@dataclass(frozen=True)
class ColoredBox(TeX):
    """Nested-aware colored info box. Background opacity grows with nesting depth.

    Mirrors the LaTeX `ColoredBox` env from HSRTReport, but the depth counter
    (`coloredBoxLevel`) is resolved at render time by walking the parent chain
    instead of relying on a global LaTeX counter.
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
        """1-indexed depth: 1 for outermost, 2 for once-nested, etc."""
        return 1 + sum(1 for p in self.parents if isinstance(p, ColoredBox))

    @property
    def background_opacity(self) -> int:
        return round((BASE_OPACITY + PER_LEVEL * self.nesting_level) * 100)

    @property
    def icon_opacity(self) -> int:
        return self.background_opacity + ICON_BOOST

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return tuple(v for v in (self.body, self.icon) if isinstance(v, TeX))

    @property
    @override
    def requires(self) -> frozenset[PackageProtocol]:
        # `calc` is required: the original env uses infix length arithmetic
        # (`\linewidth-0.5cm`, `\put(x-size,...)`) which is only valid with it.
        # `tikz` is mdframed's framemethod that actually rounds the filled
        # background when the frame lines are hidden.
        return frozenset({MDFRAMED, XCOLOR, FONTAWESOME, CALC, TIKZ})

    @property
    @override
    def rendered(self) -> str:
        # Faithful port of the HSRTReport `ColoredBox` env: a zero-height
        # picture overlays the icon at the top-left, and the body sits in a
        # narrower minipage beside it. Requires `calc` for the infix length
        # arithmetic (see `requires`).
        #
        # Nesting depth is tracked with a render-time counter (mirroring the
        # LaTeX `coloredBoxLevel`) rather than the parent chain: building the
        # wrapper nodes below re-`attach`es the body and would sever that chain
        # before the inner box renders.
        depth = _render_depth.get() + 1
        token = _render_depth.set(depth)
        try:
            # Prefer the render counter (correct for top-down rendering, where
            # building wrappers severs the parent chain); fall back to the
            # parent chain so an inner box rendered in isolation is still right.
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
                            # Zero-size overlay: the icon is drawn at its \put
                            # coordinates without reserving width, so the body
                            # minipage flows normally instead of overflowing.
                            Picture(
                                "0",
                                "0",
                                Put(
                                    f"{self.icon_offset_x}+0.2cm-{self.icon_size}",
                                    self.icon_offset_y,
                                    # `\vcenter` centres each glyph's actual
                                    # bounding box on the math axis, so circles,
                                    # triangles and ticks all line up with the
                                    # first text line regardless of metrics.
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
    return _preset(body, "info-circle", "blue", icon_offset_y="2pt")


@Registry.add
def WarningBox(body: TeX | str) -> ColoredBox:
    return _preset(
        body, "exclamation-triangle", "red", icon_offset_y="1pt", icon_offset_x="0.5pt"
    )


@Registry.add
def SuccessBox(body: TeX | str) -> ColoredBox:
    return _preset(body, "check-circle", "green")


@Registry.add
def ImportantBox(body: TeX | str) -> ColoredBox:
    return _preset(
        body,
        "exclamation-circle",
        "orange",
    )


@Registry.add
def CustomBox(body: TeX | str, icon: str | None, color: str) -> ColoredBox:
    return _preset(body, icon, color)


@Registry.add
def DiscussionBox(body: TeX | str) -> ColoredBox:
    return _preset(body, "comments", "hanblue")
