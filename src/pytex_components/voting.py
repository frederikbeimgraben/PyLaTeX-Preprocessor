from dataclasses import dataclass, field
from typing import Final, override

from pytex.commands.builtin import Textbf, VspaceStar
from pytex.commands.floats import Columnbreak, Multicols
from pytex.commands.fontawesome import FaIcon
from pytex.helpers.parenting import attach
from pytex.interface.package import PackageProtocol
from pytex.interface.tex import TeX
from pytex.model.concat import Concat
from pytex.model.package import DefinePackage
from pytex.packages import CALC, FONTAWESOME, MDFRAMED, XCOLOR
from pytex.registry import Registry

from .boxes import ColoredBox, CustomBox

__all__ = ["VotingResults"]

# `pytex.packages` has no entry for `multicol`, and the `multicols`
# environment needs that package. This module declares the package
# requirement, because `VotingResults` builds the `Multicols` node inside
# `.rendered`. The requirements of a node built there never reach the package
# collector of the document.
MULTICOL: Final = DefinePackage("multicol")


def _vote_color(yes: int, no: int) -> str:
    if yes > no:
        return "britishracinggreen"
    if yes < no:
        return "red"
    return "eggplant"


@Registry.add
@dataclass(frozen=True)
class VotingResults(TeX):
    """A box that shows the tally of a vote.

    The box prints the German labels `Ja` (yes), `Nein` (no) and
    `Enthaltung` (abstain) in three columns.

    PyTeX picks the icon color and the background color in Python from the
    counts. More yes votes give `britishracinggreen`, more no votes give
    `red`, and an equal count gives `eggplant`.

    Attributes:
        body: Text that PyTeX prints above the three columns. The default is
            the empty string, which prints nothing.
    """

    yes: Final[int]
    no: Final[int]
    abstain: Final[int]
    body: Final[TeX | str] = ""
    _parent: "TeX | None" = field(default=None, init=False, compare=False, repr=False)

    def __post_init__(self) -> None:
        attach(self, self.body)

    @property
    def color(self) -> str:
        """The xcolor name for the icon and the background, from `yes` and `no`."""
        return _vote_color(self.yes, self.no)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.body,) if isinstance(self.body, TeX) else ()

    @property
    @override
    def requires(self) -> frozenset[PackageProtocol]:
        # The nested `ColoredBox` and `CustomBox` nodes use infix length
        # arithmetic, so they need `calc`. PyTeX builds them inside
        # `.rendered`, so their own `requires` sets never reach the package
        # collector. This set names `calc` again for that reason.
        return frozenset({MDFRAMED, XCOLOR, FONTAWESOME, MULTICOL, CALC})

    @property
    @override
    def rendered(self) -> str:
        return ColoredBox(
            body=Concat(
                self.body,
                VspaceStar("-2em"),
                Multicols(
                    3,
                    Concat(
                        CustomBox(
                            Concat(Textbf("Ja:"), " ", str(self.yes)),
                            "thumbs-up",
                            "britishracinggreen",
                        ),
                        Columnbreak(),
                        CustomBox(
                            Concat(Textbf("Nein:"), " ", str(self.no)),
                            "thumbs-down",
                            "red",
                        ),
                        Columnbreak(),
                        CustomBox(
                            Concat(Textbf("Enthaltung:"), " ", str(self.abstain)),
                            None,
                            "eggplant",
                        ),
                    ),
                ),
            ),
            icon=FaIcon("vote-yea"),
            icon_color=self.color,
            icon_size="24pt",
            icon_offset_x="-0.2cm",
            background_color=self.color,
        ).rendered
