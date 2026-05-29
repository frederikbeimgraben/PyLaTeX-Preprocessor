"""Coloured callout boxes — all built on a single ColoredBox environment.

The TeX side now only defines ``ColoredBox`` (see ``tex/infoblocks.tex``); the
per-variant defaults (InfoBox / WarningBox / ...) are baked into Python and
emitted as the env's option list at the call site. The ``VotingResults``
``\\ifnum`` branching also runs in Python rather than in TeX.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import override

from pytex import BuiltinPackages, Group, IncludeTeX, Package, TeX
from pytex.model.raw import Raw, coerce_tex

_TEX_DIR = Path(__file__).parent / "tex"

_REQUIRES: frozenset[Package | str] = frozenset(
    {
        BuiltinPackages.MDFRAMED.value,
        BuiltinPackages.FONTAWESOME5.value,
        BuiltinPackages.ENVIRON.value,
        BuiltinPackages.MULTICOL.value,
        BuiltinPackages.FP.value,
    }
)


def infoblocks_preamble() -> TeX:
    """The ColoredBox environment definition (``tex/infoblocks.tex``)."""
    return IncludeTeX(_TEX_DIR / "infoblocks.tex")


@dataclass(init=False)
class _Box(TeX):
    """``\\begin{Name}[opts] body \\end{Name}`` callout wrapper."""

    name: str
    body: TeX
    options: str | None

    def __init__(
        self,
        name: str,
        body: TeX | str,
        *,
        options: str | None = None,
    ) -> None:
        self.name = name
        self.body = coerce_tex(body)
        self.options = options

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
        opt = f"[{self.options}]" if self.options is not None else ""
        return (
            f"\\begin{{{self.name}}}{opt}\n"
            f"{self.body.serialize()}\n"
            f"\\end{{{self.name}}}"
        )


def _opts(
    icon: str,
    color: str,
    *,
    fontsize: str = "24pt",
    offset_x: str = "0pt",
    offset_y: str = "0pt",
    background: str | None = None,
) -> str:
    bg = background if background is not None else color
    return (
        f"icon={{{icon}}},"
        f"icon.color={{{color}}},"
        f"icon.prefix={{}},"
        f"icon.fontsize={{{fontsize}}},"
        f"icon.offset.x={{{offset_x}}},"
        f"icon.offset.y={{{offset_y}}},"
        f"background.color={{{bg}}}"
    )


def _merge_opts(default: str, user: str | None) -> str:
    if not user:
        return default
    return f"{default},{user}"


def _body(parts: "tuple[TeX | str, ...]") -> TeX:
    if len(parts) == 1:
        return coerce_tex(parts[0])
    return Group(*parts)


def ColoredBox(*body: TeX | str, options: str | None = None) -> _Box:
    """Raw ColoredBox call. ``options`` are appended to the env defaults."""
    return _Box("ColoredBox", _body(body), options=options)


def InfoBox(*body: TeX | str, options: str | None = None) -> _Box:
    """Blue info callout (``\\faInfoCircle``)."""
    return _Box(
        "ColoredBox",
        _body(body),
        options=_merge_opts(_opts("\\faInfoCircle", "blue"), options),
    )


def WarningBox(*body: TeX | str, options: str | None = None) -> _Box:
    """Red warning callout (``\\faExclamationTriangle``)."""
    return _Box(
        "ColoredBox",
        _body(body),
        options=_merge_opts(_opts("\\faExclamationTriangle", "red"), options),
    )


def SuccessBox(*body: TeX | str, options: str | None = None) -> _Box:
    """Green success callout (``\\faCheckCircle``)."""
    return _Box(
        "ColoredBox",
        _body(body),
        options=_merge_opts(_opts("\\faCheckCircle", "green", offset_y="2pt"), options),
    )


def ImportantBox(*body: TeX | str, options: str | None = None) -> _Box:
    """Orange important callout (``\\faExclamationCircle``)."""
    return _Box(
        "ColoredBox",
        _body(body),
        options=_merge_opts(_opts("\\faExclamationCircle", "orange"), options),
    )


def DiscussionBox(*body: TeX | str, options: str | None = None) -> _Box:
    """Han-blue discussion callout (``\\faComments``)."""
    return _Box(
        "ColoredBox",
        _body(body),
        options=_merge_opts(_opts("\\faComments", "hanblue"), options),
    )


def CustomBox(body: TeX | str, icon: str, color: str) -> _Box:
    """ColoredBox with caller-chosen icon and accent colour."""
    return _Box("ColoredBox", body, options=_opts(icon, color))


def VotingResults(body: TeX | str, yes: int, no: int, abstain: int) -> _Box:
    """ColoredBox with a vote-tally trailer (Ja/Nein/Enthaltung).

    The accent colour reflects the outcome — green if motion passes, red if it
    fails, eggplant on a tie — chosen in Python instead of via ``\\ifnum``.
    """
    if yes > no:
        color = "britishracinggreen"
    elif yes < no:
        color = "red"
    else:
        color = "eggplant"

    tally_raw = (
        "\\par\\medskip\\noindent\n"
        "\\begin{minipage}[t]{0.3\\linewidth}"
        f"{CustomBox(Raw(f'\\textbf{{Ja:}} {yes}', escape_spaces=False), '\\faThumbsUp', 'britishracinggreen').serialize()}"
        "\\end{minipage}\\hfill\n"
        "\\begin{minipage}[t]{0.3\\linewidth}"
        f"{CustomBox(Raw(f'\\textbf{{Nein:}} {no}', escape_spaces=False), '\\faThumbsDown', 'red').serialize()}"
        "\\end{minipage}\\hfill\n"
        "\\begin{minipage}[t]{0.3\\linewidth}"
        f"{CustomBox(Raw(f'\\textbf{{Enthaltung:}} {abstain}', escape_spaces=False), '\\faQuestion', 'eggplant').serialize()}"
        "\\end{minipage}"
    )
    full_body = Group(coerce_tex(body), Raw(tally_raw, escape_spaces=False))
    return _Box(
        "ColoredBox",
        full_body,
        options=_opts("\\faVoteYea", color, offset_x="-0.2cm"),
    )


__all__ = [
    "infoblocks_preamble",
    "ColoredBox",
    "InfoBox",
    "WarningBox",
    "SuccessBox",
    "ImportantBox",
    "DiscussionBox",
    "CustomBox",
    "VotingResults",
]
