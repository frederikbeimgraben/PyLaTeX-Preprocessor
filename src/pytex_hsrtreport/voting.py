from dataclasses import dataclass, field
from typing import Final, override

from pytex.commands.builtin import Textbf
from pytex.commands.floats import Columnbreak, Multicols
from pytex.commands.fontawesome import FaIcon
from pytex.helpers.parenting import attach
from pytex.interface.package import PackageProtocol
from pytex.interface.tex import TeX
from pytex.model.concat import Concat
from pytex.packages import FONTAWESOME, MDFRAMED, XCOLOR
from pytex.registry import Registry

from .boxes import ColoredBox, CustomBox


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
    _parent: "TeX | None" = field(
        default=None, init=False, compare=False, repr=False
    )

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
        return frozenset({MDFRAMED, XCOLOR, FONTAWESOME})

    @property
    @override
    def rendered(self) -> str:
        return ColoredBox(
            body=Concat(
                self.body,
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
                            "question",
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
