from dataclasses import dataclass, field
from typing import Final, override

from pytex.helpers.parenting import attach
from pytex.interface.tex import TeX
from pytex.registry import Registry


@dataclass(frozen=True)
class TitlePageDataLine:
    label: str
    value: TeX | str


def _row(line: TitlePageDataLine) -> str:
    value = line.value if isinstance(line.value, str) else line.value.rendered
    return f"\\\\ \\textbf{{{line.label}}} & {value}"


@Registry.add
@dataclass
class TitlePage(TeX):
    """HSRT titlepage with abstract, keywords, and data table.

    Renders the full `titlepage` env. Logos are emitted by the LogoSet caller.
    """

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
        title_str = self.title if isinstance(self.title, str) else self.title.rendered
        abs_str = (
            self.abstract if isinstance(self.abstract, str) else self.abstract.rendered
        )
        kw_str = (
            self.keywords if isinstance(self.keywords, str) else self.keywords.rendered
        )
        rows = "".join(_row(line) for line in self.data_lines)
        return (
            r"\begin{titlepage}"
            r"\vspace{4cm}\begin{flushleft}"
            r"{\noindent\color{black}\textbf{\blenderfont\Huge\hspace*{-2.5pt}"
            f"{title_str}"
            r"}}\color{black}\vspace*{-0.5em}\rule{\textwidth}{0.5mm}"
            r"\end{flushleft}"
            r"\vspace{2em}\setstretch{1.0}"
            r"\section*{Abstract}\vspace{-1em}"
            f"{abs_str}"
            r"{\vspace*{1em}\newline\textbf{Keywords}\newline "
            f"{kw_str}}}"
            r"\vfill\noindent\setstretch{1.0}"
            r"\begin{tabular}{@{} p{30mm} p{\textwidth-30mm-2\tabcolsep}}"
            "&"
            f"{rows}"
            r"\end{tabular}"
            r"\end{titlepage}"
        )
