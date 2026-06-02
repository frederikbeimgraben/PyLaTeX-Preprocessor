from dataclasses import dataclass, field
from typing import Final, override

from pytex.commands.builtin import Textbf, Vspace
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

# `multicol` is not in pytex.packages; the multicols env needs it. Declared here
# because VotingResults builds the Multicols node inside `.rendered`, so the
# command's own requirements never reach the document's package collector.
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
    """Voting tally box. Header color picked in Python from yes/no counts."""

    yes: Final[int]
    no: Final[int]
    abstain: Final[int]
    body: Final[TeX | str] = ""
    _parent: "TeX | None" = field(default=None, init=False, compare=False, repr=False)

    def __post_init__(self) -> None:
        attach(self, self.body)

    @property
    def color(self) -> str:
        return _vote_color(self.yes, self.no)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.body,) if isinstance(self.body, TeX) else ()

    @property
    @override
    def requires(self) -> frozenset[PackageProtocol]:
        # CALC is needed because the nested ColoredBox/CustomBox use infix
        # length arithmetic; they are built inside `.rendered`, so their own
        # `requires` (which include CALC) never reach the package collector.
        return frozenset({MDFRAMED, XCOLOR, FONTAWESOME, MULTICOL, CALC})

    @property
    @override
    def rendered(self) -> str:
        return ColoredBox(
            body=Concat(
                self.body,
                Vspace("-2em", star=True),
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
