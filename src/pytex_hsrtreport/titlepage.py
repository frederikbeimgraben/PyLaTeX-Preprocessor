"""Title page — fully declarative, built from :mod:`pytex` and :mod:`pytex_tikz`.

No hand-formatted multi-line strings: the ``\\maketitle`` body is a
:class:`Block` of native TeX nodes (``\\section*``, ``\\vspace``, environments,
``TikzPicture``, ``Node`` …). The data-table token machinery still goes through
small ``\\DeclareRobustCommand`` definitions but they too are emitted as
:class:`DeclareRobustCommand` / :class:`NewCommand` nodes inside a
:class:`MakeAtLetter` wrapper.
"""

from pytex import (
    Command,
    DeclareRobustCommand,
    Group,
    Href,
    MakeAtLetter,
    NewCommand,
    ProvideCommand,
    RenewCommand,
    TeX,
)
from pytex.library import Environment, IncludeGraphics
from pytex.model.raw import Raw, coerce_tex
from pytex_komascript.model import Block
from pytex_tikz import Coordinate, Node, TikzPicture

from .logos import (
    DEFAULT_GLOBAL_SCALE,
    DEFAULT_MAIN_SCALE,
    titlepage_logo_node,
    titlepage_main_height,
)
from .paths import DummyFootPath


def _heart_node() -> Node:
    """The ``Made with ♥ in LaTeX`` link node in the south-east corner."""
    label = Raw(
        "\\tiny\\color{gray}\\blenderfont Made with "
        "{\\ensuremath\\heartsuit} in \\LaTeX",
        escape_spaces=False,
    )
    return Node(
        Href("https://github.com/frederikbeimgraben/HSRT-Report", label),
        options=(
            "anchor=south east, inner sep=0pt, "
            "xshift=-0.1cm, yshift=0.1cm"
        ),
        name="heart",
        at=Coordinate.page("south east"),
    )


def _dummy_anchor_node(main_height: str) -> Node:
    """Invisible anchor node (logo0) hosting DUMMY_FOOT.png."""
    return Node(
        IncludeGraphics(str(DummyFootPath), height=main_height),
        options=(
            "anchor=north west, inner sep=0pt, "
            "xshift=\\leftmargin, yshift=-1.5cm, opacity=0"
        ),
        name="logo0",
        at=Coordinate.page("north west"),
    )


def _title_rule() -> TeX:
    """The huge title line and its decorative bottom rule, baked as one Group.

    The contents are nearly all primitive TeX (font size, color, weight) so
    they live in a single :class:`Raw` rather than a chain of micro-nodes.
    """
    return Group(
        Raw(
            "\\noindent\\color{black}\\textbf{\\blenderfont\\Huge"
            "\\hspace*{-2.5pt}\\@title}",
            escape_spaces=False,
        ),
        Raw(
            "\\color{black}\\vspace*{-0.5em}\\rule{\\textwidth}{0.5mm}",
            escape_spaces=False,
        ),
    )


def _abstract_section() -> TeX:
    return Block(
        Raw("\\section*{Abstract}\\vspace{-1em}\\titlepageabstract", escape_spaces=False),
        Group(
            Raw(
                "\\vspace*{1em}\\newline\\textbf{Keywords}\\newline\\titlepagekeywords",
                escape_spaces=False,
            ),
        ),
    )


def _maketitle_body(
    resolved: list[tuple[str, float]],
    *,
    global_scale: float,
    main_scale: float,
) -> TeX:
    """Compose the renewcommand body: tikz overlay + title + abstract + table."""
    logo_nodes: list[TeX] = [_heart_node(), _dummy_anchor_node(
        titlepage_main_height(main_scale, global_scale)
    )]
    logo_nodes.extend(
        titlepage_logo_node(i, name, scale, global_scale)
        for i, (name, scale) in enumerate(resolved, start=1)
    )

    return Block(
        # \def\istitlepage=\true is the original .cls trick used by
        # \ifdefstring{\istitlepage}{\true}{...}{...} checks elsewhere; the
        # weird parameter-text form is unavoidable as a native primitive.
        Raw("\\def\\istitlepage=\\true", escape_spaces=False),
        Command("pagenumbering", "arabic"),
        ProvideCommand(
            "titlepageabstract",
            "Dies ist ein Beispiel für ein Abstract.",
        ),
        ProvideCommand(
            "titlepagekeywords",
            "Seminararbeit, Beispiel",
        ),
        Environment(
            "titlepage",
            Block(
                TikzPicture(*logo_nodes, options="overlay, remember picture"),
                Command("vspace", "4cm"),
                Environment("flushleft", _title_rule()),
                Command("vspace", "2em"),
                Command("setstretch", "1.0"),
                _abstract_section(),
                Command("vfill"),
                Raw("\\noindent\\setstretch{1.0}", escape_spaces=False),
                Command("GetTitlePageDataTable"),
            ),
        ),
    )


def _data_table_machinery() -> TeX:
    """Token-register data-table primitives. Wrapped in MakeAtLetter."""
    return MakeAtLetter(
        Block(
            NewCommand("createdon", "\\gdef\\@createdon{#1}", n_args=1),
            Raw("\\newtoks\\titlePageData", escape_spaces=False),
            Raw("\\def\\tand{&}", escape_spaces=False),
            Raw("\\titlePageData={\\tand}", escape_spaces=False),
            DeclareRobustCommand(
                "AddTitlePageDataSpace",
                "\\titlePageData=\\expandafter{\\the\\titlePageData \\vspace{#1}}",
                n_args=1,
            ),
            DeclareRobustCommand(
                "AddTitlePageDataLine",
                "\\titlePageData=\\expandafter{\\the\\titlePageData\\\\ "
                "\\textbf{#1}\\tand #2}",
                n_args=2,
            ),
            DeclareRobustCommand(
                "GetTitlePageDataTable",
                "\\begin{tabular}{@{} p{30mm} p{\\textwidth-30mm-2\\tabcolsep}}"
                "\\the\\titlePageData\\end{tabular}",
            ),
        )
    )


def title_page_defs(
    resolved: list[tuple[str, float]],
    *,
    global_scale: float = DEFAULT_GLOBAL_SCALE,
    main_scale: float = DEFAULT_MAIN_SCALE,
) -> TeX:
    """Title-page preamble: data table primitives + ``\\renewcommand{\\maketitle}``."""
    return Block(
        _data_table_machinery(),
        RenewCommand(
            "maketitle",
            _maketitle_body(
                resolved,
                global_scale=global_scale,
                main_scale=main_scale,
            ),
        ),
    )


def _content(value: TeX | str) -> TeX:
    return coerce_tex(value) if isinstance(value, str) else value


def title_metadata_block(
    *,
    title: TeX | str | None,
    author: TeX | str | None,
    created_on: str | None,
    abstract: TeX | str | None,
    keywords: TeX | str | None,
    module_name: str | None,
    data_lines: "list[tuple[str, TeX | str]] | None",
) -> TeX:
    """``\\title`` / ``\\author`` / ``\\createdon`` / abstract / keywords / table lines.

    Each metadata command is its own TeX node; an absent field omits its line
    entirely.
    """
    parts: list[TeX] = []
    if title is not None:
        parts.append(Command("title", _content(title)))
    if author is not None:
        parts.append(Command("author", _content(author)))
    if created_on is not None:
        parts.append(Command("createdon", created_on))
    if abstract is not None:
        parts.append(NewCommand("titlepageabstract", _content(abstract)))
    if keywords is not None:
        parts.append(NewCommand("titlepagekeywords", _content(keywords)))
    if module_name is not None:
        parts.append(NewCommand("modulename", module_name))
    for label, content in data_lines or []:
        parts.append(Command("AddTitlePageDataLine", label, _content(content)))
        parts.append(Command("AddTitlePageDataSpace", "5pt"))
    return Block(*parts)


__all__ = [
    "title_page_defs",
    "title_metadata_block",
]
