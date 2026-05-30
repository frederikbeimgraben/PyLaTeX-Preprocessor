"""Title page — fully declarative, built from :mod:`pytex` and :mod:`pytex_tikz`.

No hand-formatted multi-line strings: the ``\\maketitle`` body is a
:class:`Block` of native TeX nodes (``\\section*``, ``\\vspace``, environments,
:class:`TikzPicture`, :class:`Node` …). The data-table token machinery uses
native :class:`NewToks` / :class:`Def` / :class:`AssignToks` /
:class:`DeclareRobustCommand` nodes inside a :class:`MakeAtLetter` wrapper.
"""

from pytex import (
    AssignToks,
    Bold,
    Command,
    DeclareRobustCommand,
    Def,
    Group,
    Href,
    MakeAtLetter,
    NewCommand,
    NewToks,
    ProvideCommand,
    RenewCommand,
    TabularEnv,
    TeX,
)
from pytex.library import IncludeGraphics
from pytex.library.environments import Environment
from pytex.model.raw import coerce_tex
from pytex_komascript.model import Block
from pytex_tikz import Coordinate, Node, TikzPicture

from .logos import (
    DEFAULT_GLOBAL_SCALE,
    DEFAULT_MAIN_SCALE,
    titlepage_logo_node,
    titlepage_main_height,
)
from .paths import DummyFootPath


def _heart_label() -> TeX:
    """The ``Made with ♥ in LaTeX`` link label, built from native nodes."""
    return Block(
        Command("tiny"),
        Command("color", "gray"),
        Command("blenderfont"),
        coerce_tex("Made with "),
        Group(Command("ensuremath", Command("heartsuit"))),
        coerce_tex(" in "),
        Command("LaTeX"),
    )


def _heart_node() -> Node:
    """The ``Made with ♥ in LaTeX`` link node in the south-east corner."""
    return Node(
        Href("https://github.com/frederikbeimgraben/HSRT-Report", _heart_label()),
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
    """The huge title line and its decorative bottom rule, built natively."""
    title_line = Block(
        Command("noindent"),
        Command("color", "black"),
        Bold(
            Block(
                Command("blenderfont"),
                Command("Huge"),
                Command("hspace*", "-2.5pt"),
                Command("@title"),
            )
        ),
    )
    rule_line = Block(
        Command("color", "black"),
        Command("vspace*", "-0.5em"),
        Command("rule", "\\textwidth", "0.5mm"),
    )
    return Group(title_line, rule_line)


def _abstract_section() -> TeX:
    keywords_group = Group(
        Command("vspace*", "1em"),
        Command("newline"),
        Bold("Keywords"),
        Command("newline"),
        Command("titlepagekeywords"),
    )
    return Block(
        Command("section*", "Abstract"),
        Command("vspace", "-1em"),
        Command("titlepageabstract"),
        keywords_group,
    )


def _maketitle_body(
    resolved: list[tuple[str, float]],
    *,
    global_scale: float,
    main_scale: float,
) -> TeX:
    """Compose the renewcommand body: tikz overlay + title + abstract + table."""
    logo_nodes: list[Node] = [
        _heart_node(),
        _dummy_anchor_node(titlepage_main_height(main_scale, global_scale)),
    ]
    logo_nodes.extend(
        titlepage_logo_node(i, name, scale, global_scale)
        for i, (name, scale) in enumerate(resolved, start=1)
    )

    return Block(
        # Original .cls trick: \def\istitlepage=\true with empty body so a
        # later \ifdefstring{\istitlepage}{\true}{...}{...} never matches.
        Def("istitlepage", "", param_text="=\\true"),
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
                Command("noindent"),
                Command("setstretch", "1.0"),
                Command("GetTitlePageDataTable"),
            ),
        ),
    )


def _data_table_machinery() -> TeX:
    """Token-register data-table primitives. Wrapped in MakeAtLetter."""
    add_space_body = AssignToks(
        "titlePageData",
        Command("vspace", "#1"),
        expand_after=True,
    )
    add_line_body = AssignToks(
        "titlePageData",
        Block(
            Command("\\"),
            coerce_tex(" "),
            Bold("#1"),
            Command("tand"),
            coerce_tex(" #2"),
        ),
        expand_after=True,
    )
    get_table_body = TabularEnv(
        "@{} p{30mm} p{\\textwidth-30mm-2\\tabcolsep}",
        Block(Command("the"), Command("titlePageData")),
    )

    return MakeAtLetter(
        Block(
            NewCommand(
                "createdon",
                Def("@createdon", "#1", global_=True),
                n_args=1,
            ),
            NewToks("titlePageData"),
            Def("tand", "&"),
            AssignToks("titlePageData", Command("tand")),
            DeclareRobustCommand("AddTitlePageDataSpace", add_space_body, n_args=1),
            DeclareRobustCommand("AddTitlePageDataLine", add_line_body, n_args=2),
            DeclareRobustCommand("GetTitlePageDataTable", get_table_body),
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
