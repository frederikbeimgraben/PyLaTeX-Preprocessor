from dataclasses import dataclass, field
from typing import Final, override

from pytex.commands.builtin import Hspace, Noindent, Vspace
from pytex.commands.colors import Color
from pytex.commands.fontawesome import FaIcon
from pytex.commands.floats import Minipage
from pytex.commands.font import Fontsize, Selectfont
from pytex.commands.mdframed import Mdframed
from pytex.commands.picture import Picture, Put
from pytex.helpers.parenting import attach
from pytex.interface.package import PackageProtocol
from pytex.interface.tex import TeX
from pytex.model.concat import Concat
from pytex.packages import FONTAWESOME5, MDFRAMED, XCOLOR
from pytex.registry import Registry

_BASE_OPACITY: Final[float] = 0.05
_PER_LEVEL: Final[float] = 0.075
_ICON_BOOST: Final[int] = 20


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
    _parent: "TeX | None" = field(
        default=None, init=False, compare=False, repr=False
    )

    def __post_init__(self) -> None:
        attach(self, self.body, self.icon)

    @property
    def nesting_level(self) -> int:
        """1-indexed depth: 1 for outermost, 2 for once-nested, etc."""
        return 1 + sum(1 for p in self.parents if isinstance(p, ColoredBox))

    @property
    def background_opacity(self) -> int:
        return round((_BASE_OPACITY + _PER_LEVEL * self.nesting_level) * 100)

    @property
    def icon_opacity(self) -> int:
        return self.background_opacity + _ICON_BOOST

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        out: list[TeX] = []
        if isinstance(self.body, TeX):
            out.append(self.body)
        if isinstance(self.icon, TeX):
            out.append(self.icon)
        return tuple(out)

    @property
    @override
    def requires(self) -> frozenset[PackageProtocol]:
        return frozenset({MDFRAMED, XCOLOR, FONTAWESOME5})

    @property
    @override
    def rendered(self) -> str:
        return self._build().rendered

    def _build(self) -> TeX:
        bg = f"{self.background_color}!{self.background_opacity}"
        ic = f"{self.icon_color}!{self.icon_opacity}"

        icon_block = Put(
            f"{self.icon_offset_x}-{self.icon_size}",
            f"{self.icon_offset_y}-0.7cm",
            Concat(
                Fontsize(self.icon_size, self.icon_size),
                Selectfont(),
                Color(ic),
                self.icon,
            ),
        )

        inner_body = Minipage(
            r"\linewidth-0.5cm",
            Concat(
                Vspace(r"0.5\baselineskip"),
                self.body,
                Vspace(r"0.5\baselineskip"),
            ),
        )

        mdframed_body = Concat(
            Picture(r"\textwidth", "0", icon_block),
            Hspace("0.25cm", star=True),
            inner_body,
        )

        framed = Mdframed(
            mdframed_body,
            options={
                "backgroundcolor": "{" + bg + "}",
                "hidealllines": "true",
                "skipabove": r"0.7\baselineskip",
                "skipbelow": r"0.7\baselineskip",
                "splitbottomskip": "2pt",
                "splittopskip": "4pt",
                "roundcorner": "5pt",
            },
        )

        return Concat(
            Vspace(r"0.5\baselineskip", star=True),
            Noindent(),
            Minipage(r"\linewidth", framed),
        )


def _preset(
    body: TeX | str,
    icon_name: str,
    color: str,
    icon_size: str = "24pt",
    icon_offset_x: str = "0pt",
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
    return _preset(body, "info-circle", "blue")


@Registry.add
def WarningBox(body: TeX | str) -> ColoredBox:
    return _preset(body, "exclamation-triangle", "red")


@Registry.add
def SuccessBox(body: TeX | str) -> ColoredBox:
    return _preset(body, "check-circle", "green", icon_offset_y="2pt")


@Registry.add
def ImportantBox(body: TeX | str) -> ColoredBox:
    return _preset(body, "exclamation-circle", "orange")


@Registry.add
def CustomBox(body: TeX | str, icon: str, color: str) -> ColoredBox:
    return _preset(body, icon, color)


@Registry.add
def DiscussionBox(body: TeX | str) -> ColoredBox:
    return _preset(body, "comments", "hanblue")
