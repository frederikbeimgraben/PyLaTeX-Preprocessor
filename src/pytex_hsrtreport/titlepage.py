from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Final, override

from pytex.commands.builtin import (
    Blenderfont,
    Newline,
    Noindent,
    Rule,
    SectionStar,
    Textbf,
    Vfill,
    Vspace,
    VspaceStar,
)
from pytex.commands.colors import SelectColor
from pytex.commands.floats import Titlepage as TitlepageEnv
from pytex.commands.font import Huge
from pytex.commands.setspace import Setstretch
from pytex.commands.tables import Tabular
from pytex.helpers.parenting import attach
from pytex.interface.tex import TeX
from pytex.model.concat import Concat
from pytex.model.empty import Empty
from pytex.model.environment import Environment
from pytex.model.raw import Raw
from pytex.registry import Registry

from .logos import titlepage_logo_overlay


def _is_blank(node: TeX | str) -> bool:
    """True for an empty string or the `Empty` node — used to skip empty
    title-page sections (a protocol has no abstract or keywords)."""
    if isinstance(node, str):
        return not node.strip()
    return node is Empty


__all__ = ["TitlePage", "TitlePageDataLine"]


@dataclass(frozen=True)
class TitlePageDataLine:
    label: str
    value: TeX | str


def _data_table_body(lines: tuple[TitlePageDataLine, ...]) -> TeX:
    return Concat(
        "&",
        *(
            part
            for line in lines
            for part in (Newline(), Textbf(line.label), " & ", line.value)
        ),
    )


@Registry.add
@dataclass
class TitlePage(TeX):
    """HSRT titlepage with abstract, keywords, and data table.

    ``logo_names`` drives a tikz overlay that chains logos left-to-right from
    the top-left corner of the page, mirroring the ``\\foreach`` loop in
    ``tmp/Pages/Titlepage.tex`` (loop unrolled in Python).
    """

    title: Final[TeX | str]
    abstract: Final[TeX | str] = ""
    keywords: Final[TeX | str] = ""
    data_lines: Final[tuple[TitlePageDataLine, ...]] = ()
    logo_names: Final[tuple[str, ...]] = ()
    abstract_heading: Final[str] = "Abstract"
    keywords_heading: Final[str] = "Keywords"
    _parent: "TeX | None" = field(default=None, init=False, compare=False, repr=False)

    def __post_init__(self) -> None:
        attach(self, self.title, self.abstract, self.keywords)
        for line in self.data_lines:
            attach(self, line.value)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        candidates = (
            self.title,
            self.abstract,
            self.keywords,
            *(line.value for line in self.data_lines),
        )
        return tuple(v for v in candidates if isinstance(v, TeX))

    def _title_block(self) -> TeX:
        return Environment(
            "flushleft",
            Concat(
                Raw(r"\hyphenpenalty=10000\exhyphenpenalty=10000"),
                Noindent(),
                SelectColor("black"),
                Textbf(
                    Concat(
                        Blenderfont(),
                        Huge(),
                        # A plain control-word terminator, not an optical kern:
                        # the old \hspace*{-2.5pt} shifted only the first line,
                        # leaving a wrapped title's later lines misaligned with
                        # it and the rule. The space just ends \Huge (TeX gobbles
                        # it) so the title's first word is not read as a macro.
                        Raw(" "),
                        self.title,
                    )
                ),
                Raw(r"\par"),
                Vspace("-0.5em"),
                Rule(r"\textwidth", "0.5mm"),
            ),
        )

    def _content(self) -> Iterator[TeX | str]:
        # Tikz overlay: logos chained left-to-right from the top-left corner,
        # matching tmp/Pages/Titlepage.tex but with the foreach unrolled here.
        yield Raw(titlepage_logo_overlay(self.logo_names), allow_replacements=False)
        yield Vspace("4cm")
        yield self._title_block()
        yield Vspace("2em")
        yield Setstretch("1.0")
        # Abstract and keywords are optional — skip the labels when empty
        # (e.g. a meeting protocol has neither).
        if not _is_blank(self.abstract):
            yield SectionStar(self.abstract_heading)
            yield Vspace("-1em")
            yield self.abstract
            yield VspaceStar("1em")
        if not _is_blank(self.keywords):
            yield Raw(r"\par\noindent ")
            yield Textbf(self.keywords_heading)
            yield Raw(r"\par\noindent ")
            yield self.keywords
        yield Vfill()
        yield Noindent()
        yield Setstretch("1.0")
        yield Tabular(
            r"@{} p{30mm} p{\dimexpr\textwidth-30mm-2\tabcolsep\relax} @{}",
            _data_table_body(self.data_lines),
        )

    @property
    @override
    def rendered(self) -> str:
        # `\HSRTTitlePagetrue` while the titlepage ships out so footer_logo_hook
        # suppresses the bottom-right footer logos on this page only; reset
        # after \end{titlepage} (which \clearpages while the flag is still set).
        return Concat(
            Raw(r"\HSRTTitlePagetrue", allow_replacements=False),
            TitlepageEnv(Concat(*self._content())),
            Raw(r"\HSRTTitlePagefalse", allow_replacements=False),
        ).rendered
