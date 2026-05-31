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
from pytex.commands.font import HugeBig
from pytex.commands.colors import SelectColor
from pytex.commands.floats import Titlepage as TitlepageEnv
from pytex.commands.setspace import Setstretch
from pytex.commands.tables import Tabular
from pytex.helpers.parenting import attach
from pytex.interface.tex import TeX
from pytex.model.concat import Concat
from pytex.model.environment import Environment
from pytex.registry import Registry


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
    """HSRT titlepage with abstract, keywords, and data table."""

    title: Final[TeX | str]
    abstract: Final[TeX | str] = ""
    keywords: Final[TeX | str] = ""
    data_lines: Final[tuple[TitlePageDataLine, ...]] = ()
    _parent: "TeX | None" = field(
        default=None, init=False, compare=False, repr=False
    )

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
        return TitlepageEnv(
            Concat(
                Vspace("4cm"),
                Environment(
                    "flushleft",
                    Concat(
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
                        SelectColor("black"),
                        Vspace("-0.5em", star=True),
                        Rule(r"\textwidth", "0.5mm"),
                    ),
                ),
                Vspace("2em"),
                Setstretch("1.0"),
                SectionStar("Abstract"),
                Vspace("-1em"),
                self.abstract,
                Vspace("1em", star=True),
                Newline(),
                Textbf("Keywords"),
                Newline(),
                self.keywords,
                Vfill(),
                Noindent(),
                Setstretch("1.0"),
                Tabular(
                    r"@{} p{30mm} p{\textwidth-30mm-2\tabcolsep}",
                    _data_table_body(self.data_lines),
                ),
            )
        ).rendered
