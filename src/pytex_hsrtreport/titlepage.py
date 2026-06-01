from dataclasses import dataclass, field
from typing import Final, override

from pytex.commands.builtin import (
    Blenderfont,
    Hspace,
    Newline,
    Noindent,
    Rule,
    SectionStar,
    Textbf,
    Vfill,
    Vspace,
)
from pytex.commands.colors import SelectColor
from pytex.commands.floats import Titlepage as TitlepageEnv
from pytex.commands.font import HugeBig
from pytex.commands.setspace import Setstretch
from pytex.commands.tables import Tabular
from pytex.helpers.parenting import attach
from pytex.interface.tex import TeX
from pytex.model.concat import Concat
from pytex.model.environment import Environment
from pytex.model.raw import Raw
from pytex.registry import Registry

from .logos import titlepage_logo_overlay


@dataclass(frozen=True)
class TitlePageDataLine:
    label: str
    value: TeX | str


def _data_table_body(lines: tuple[TitlePageDataLine, ...]) -> TeX:
    parts: list[TeX | str] = ["&"]
    for line in lines:
        parts.extend((Newline(), Textbf(line.label), " & ", line.value))
    return Concat(*parts)


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
    _parent: "TeX | None" = field(default=None, init=False, compare=False, repr=False)

    def __post_init__(self) -> None:
        attach(self, self.title, self.abstract, self.keywords)
        for line in self.data_lines:
            attach(self, line.value)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        out: list[TeX] = []
        for v in (self.title, self.abstract, self.keywords):
            if isinstance(v, TeX):
                out.append(v)
        for line in self.data_lines:
            if isinstance(line.value, TeX):
                out.append(line.value)
        return tuple(out)

    @property
    @override
    def rendered(self) -> str:
        # Tikz overlay: logos chained left-to-right from the top-left corner,
        # matching tmp/Pages/Titlepage.tex but with the foreach unrolled here.
        logo_overlay = Raw(
            titlepage_logo_overlay(self.logo_names),
            allow_replacements=False,
        )
        # Flag true while the titlepage ships out so footer_logo_hook
        # suppresses the bottom-right footer logos on this page only.
        # Reset after \end{titlepage} (which \clearpages, shipping the page
        # while the flag is still true).
        return Concat(
            Raw(r"\HSRTTitlePagetrue", allow_replacements=False),
            TitlepageEnv(
                Concat(
                    logo_overlay,
                    Vspace("4cm"),
                    Environment(
                        "flushleft",
                        Concat(
                            Raw(r"\hyphenpenalty=10000\exhyphenpenalty=10000"),
                            Noindent(),
                            SelectColor("black"),
                            Textbf(
                                Concat(
                                    Blenderfont(),
                                    HugeBig(),
                                    Hspace("-2.5pt", star=True),
                                    self.title,
                                )
                            ),
                            Raw(r"\par"),
                            Vspace("-0.5em"),
                            Rule(r"\textwidth", "0.5mm"),
                        ),
                    ),
                    Vspace("2em"),
                    Setstretch("1.0"),
                    SectionStar("Abstract"),
                    Vspace("-1em"),
                    self.abstract,
                    Vspace("1em", star=True),
                    Raw(r"\par\noindent "),
                    Textbf("Keywords"),
                    Raw(r"\par\noindent "),
                    self.keywords,
                    Vfill(),
                    Noindent(),
                    Setstretch("1.0"),
                    Tabular(
                        r"@{} p{30mm} p{\dimexpr\textwidth-30mm-2\tabcolsep\relax} @{}",
                        _data_table_body(self.data_lines),
                    ),
                )
            ),
            Raw(r"\HSRTTitlePagefalse", allow_replacements=False),
        ).rendered
