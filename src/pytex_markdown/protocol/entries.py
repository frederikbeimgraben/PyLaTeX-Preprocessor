"""Protocol entry factories, styled to match the HSRTReport callout language.

Each entry is a coloured box (or, for votes, the existing ``VotingResults``
tally) so a protocol reads with the same visual vocabulary as a report. Labels
are German, matching the STUPA/AStA context.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pytex.commands.builtin import Textbf, Textit
from pytex.commands.colors import Textcolor
from pytex.commands.fontawesome import FaIcon
from pytex.model.concat import Concat
from pytex.registry import Registry
from pytex_components.boxes import ColoredBox
from pytex_components.voting import VotingResults

if TYPE_CHECKING:
    from pytex.interface.tex import TeX

__all__ = [
    "ActionItem",
    "Deadline",
    "Decision",
    "Timestamp",
    "Vote",
]


def _labelled_box(
    label: str,
    body: TeX | str,
    *,
    icon: str,
    color: str,
) -> TeX:
    """A ColoredBox whose body is prefixed with a bold label, matching _preset."""
    return ColoredBox(
        body=Concat(Textbf(f"{label}: "), body),
        icon=FaIcon(icon),
        icon_color=color,
        icon_size="24pt",
        icon_offset_x="1.5pt",
        background_color=color,
    )


@Registry.add
def Decision(body: TeX | str) -> TeX:
    """A resolution/`Beschluss` box (gavel, HSRT green)."""
    return _labelled_box("Beschluss", body, icon="gavel", color="britishracinggreen")


@Registry.add
def Deadline(body: TeX | str, due: str | None = None) -> TeX:
    """A `Frist` (deadline) box. `due` is appended in parentheses when given."""
    content = Concat(body, Textit(f" (bis {due})")) if due else body
    return _labelled_box("Frist", content, icon="hourglass-half", color="orange")


@Registry.add
def ActionItem(
    body: TeX | str,
    who: str | None = None,
    due: str | None = None,
) -> TeX:
    """An `Aufgabe` (action item) box with optional assignee and due date."""
    meta = ", ".join(
        part
        for part in (
            f"Zuständig: {who}" if who else "",
            f"Frist: {due}" if due else "",
        )
        if part
    )
    content = Concat(body, Textit(f" ({meta})")) if meta else body
    return _labelled_box("Aufgabe", content, icon="clipboard-check", color="navyblue")


@Registry.add
def Vote(
    yes: int,
    no: int,
    abstain: int = 0,
    body: TeX | str = "",
) -> TeX:
    """A voting tally, reusing the report's `VotingResults` box."""
    return VotingResults(yes=yes, no=no, abstain=abstain, body=body)


@Registry.add
def Timestamp(time: str) -> TeX:
    """Inline timestamp: a clock glyph plus the time, in HSRT blue."""
    return Textcolor("hanblue", Concat(FaIcon("clock"), " ", Textbf(time)))
