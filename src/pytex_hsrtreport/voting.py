from dataclasses import dataclass, field
from typing import Final, override

from pytex.commands.fontawesome import FaIcon
from pytex.helpers.parenting import attach
from pytex.interface.package import PackageProtocol
from pytex.interface.tex import TeX
from pytex.model.concat import Concat
from pytex.model.control_sequence import Parameter
from pytex.model.environment import Environment
from pytex.model.raw import Raw
from pytex.packages import FONTAWESOME5, MDFRAMED, XCOLOR
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
        return frozenset({MDFRAMED, XCOLOR, FONTAWESOME5})

    @property
    @override
    def rendered(self) -> str:
        return _build(self).rendered


def _build(vr: "VotingResults") -> TeX:
    columns = Environment(
        "multicols",
        Concat(
            CustomBox(Raw(f"\\textbf{{Ja:}} {vr.yes}"), "thumbs-up", "britishracinggreen"),
            Raw("\\columnbreak"),
            CustomBox(Raw(f"\\textbf{{Nein:}} {vr.no}"), "thumbs-down", "red"),
            Raw("\\columnbreak"),
            CustomBox(Raw(f"\\textbf{{Enthaltung:}} {vr.abstain}"), "question", "eggplant"),
        ),
        (Parameter("3"),),
    )
    inner = Concat(vr.body, columns)
    return ColoredBox(
        body=inner,
        icon=FaIcon("vote-yea"),
        icon_color=vr.color,
        icon_size="24pt",
        icon_offset_x="-0.2cm",
        background_color=vr.color,
    )
