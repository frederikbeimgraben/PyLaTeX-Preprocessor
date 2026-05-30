"""Title page — fully declarative, built from :mod:`pytex` and :mod:`pytex_tikz`.

Everything that the original ``HSRTReport.cls`` deferred through ``\\newcommand``s
(``\\titlepageabstract``, ``\\titlepagekeywords``, ``\\AddTitlePageDataLine`` /
``\\AddTitlePageDataSpace`` / ``\\GetTitlePageDataTable``) is expanded in
Python: the abstract, keywords and data table are baked directly into the
``\\maketitle`` body. Net effect on the TeX side is fewer macro definitions
and one less expansion pass at compile time.
"""

from pytex import (
    Bold,
    Command,
    Def,
    Group,
    Href,
    MakeAtLetter,
    RenewCommand,
    TabularEnv,
    TeX,
)
from pytex.library import IncludeGraphics
from pytex.library.environments import Environment
from pytex.model.raw import Raw, coerce_tex
from pytex_komascript.model import Block, Concat
from pytex_tikz import Coordinate, Node, TikzPicture

from .logos import (
    DEFAULT_GLOBAL_SCALE,
    DEFAULT_MAIN_SCALE,
    titlepage_logo_node,
    titlepage_main_height,
)
from .paths import DummyFootPath


def _CoerceText(value: TeX | str | None, default: str = "") -> TeX:
    return coerce_tex(default if value is None else value)


def _HeartLabel() -> TeX:
    return Block(
        Command("tiny"),
        Command("color", "gray"),
        Command("blenderfont"),
        coerce_tex("Made with "),
        Group(Command("ensuremath", Command("heartsuit"))),
        coerce_tex(" in "),
        Command("LaTeX"),
    )


def _HeartNode() -> Node:
    return Node(
        Href("https://github.com/frederikbeimgraben/HSRT-Report", _HeartLabel()),
        options=(
            "anchor=south east, inner sep=0pt, "
            "xshift=-0.1cm, yshift=0.1cm"
        ),
        name="heart",
        at=Coordinate.page("south east"),
    )


def _DummyAnchorNode(main_height: str) -> Node:
    return Node(
        IncludeGraphics(str(DummyFootPath), height=main_height),
        options=(
            "anchor=north west, inner sep=0pt, "
            "xshift=\\leftmargin, yshift=-1.5cm, opacity=0"
        ),
        name="logo0",
        at=Coordinate.page("north west"),
    )


def _TitleRule() -> TeX:
    return Group(
        Block(
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
        ),
        Block(
            Command("color", "black"),
            Command("vspace*", "-0.5em"),
            Command("rule", "\\textwidth", "0.5mm"),
        ),
    )


def _AbstractSection(abstract: TeX, keywords: TeX) -> TeX:
    return Block(
        Command("section*", "Abstract"),
        Command("vspace", "-1em"),
        abstract,
        Group(
            Command("vspace*", "1em"),
            Command("newline"),
            Bold("Keywords"),
            Command("newline"),
            keywords,
        ),
    )


def _DataTable(data_lines: "tuple[tuple[str, TeX], ...]") -> TeX:
    """Title-page metadata table built inline — no toks register, no
    ``\\AddTitlePageDataLine`` macros. Each ``(label, value)`` row becomes
    ``\\textbf{label} & value \\\\`` plus a ``\\vspace{5pt}`` spacer.

    The cell separators (`` & ``, `` \\\\ ``) need literal spaces; that's
    raw TeX punctuation, so :class:`Raw` is the right leaf escape here.
    """
    return TabularEnv(
        "@{} p{30mm} p{\\textwidth-30mm-2\\tabcolsep}",
        Block(
            *(
                Concat(
                    Bold(label),
                    Raw(" & ", escape_spaces=False),
                    value,
                    Raw(" \\\\ ", escape_spaces=False),
                    Command("vspace", "5pt"),
                )
                for label, value in data_lines
            )
        ),
    )


def _CreatedOnDef(created_on: str | None) -> TeX:
    """``\\gdef\\@createdon{<value>}`` inside MakeAtLetter, or nothing."""
    if created_on is None:
        return Block()
    return MakeAtLetter(Def("@createdon", created_on, global_=True))


def _IsTitlepageDef() -> TeX:
    """Original .cls trick: ``\\def\\istitlepage=\\true`` with empty body."""
    return Def("istitlepage", "", param_text="=\\true")


def _MaketitleBody(
    resolved: list[tuple[str, float]],
    *,
    global_scale: float,
    main_scale: float,
    abstract: TeX,
    keywords: TeX,
    data_lines: tuple[tuple[str, TeX], ...],
) -> TeX:
    logo_nodes: tuple[Node, ...] = (
        _HeartNode(),
        _DummyAnchorNode(titlepage_main_height(main_scale, global_scale)),
        *(
            titlepage_logo_node(i, name, scale, global_scale)
            for i, (name, scale) in enumerate(resolved, start=1)
        ),
    )
    return Block(
        _IsTitlepageDef(),
        Command("pagenumbering", "arabic"),
        Environment(
            "titlepage",
            Block(
                TikzPicture(*logo_nodes, options="overlay, remember picture"),
                Command("vspace", "4cm"),
                Environment("flushleft", _TitleRule()),
                Command("vspace", "2em"),
                Command("setstretch", "1.0"),
                _AbstractSection(abstract, keywords),
                Command("vfill"),
                Command("noindent"),
                Command("setstretch", "1.0"),
                _DataTable(data_lines),
            ),
        ),
    )


def TitlePageDefs(
    resolved: list[tuple[str, float]],
    *,
    title: TeX | str | None,
    author: TeX | str | None,
    created_on: str | None,
    abstract: TeX | str | None,
    keywords: TeX | str | None,
    data_lines: "tuple[tuple[str, TeX | str], ...] | None" = None,
    global_scale: float = DEFAULT_GLOBAL_SCALE,
    main_scale: float = DEFAULT_MAIN_SCALE,
) -> TeX:
    """``\\title`` / ``\\author`` / ``\\@createdon`` + ``\\renewcommand{\\maketitle}``.

    Everything user-facing (title, author, abstract, keywords, table rows)
    is expanded in Python and baked into the maketitle body — no
    ``\\newcommand{\\titlepageabstract}`` shim, no ``\\AddTitlePageDataLine``
    toks-register machinery.
    """
    abstract_tex = _CoerceText(abstract, "Dies ist ein Beispiel für ein Abstract.")
    keywords_tex = _CoerceText(keywords, "Seminararbeit, Beispiel")
    coerced_rows: tuple[tuple[str, TeX], ...] = tuple(
        (label, coerce_tex(content)) for label, content in (data_lines or ())
    )
    return Block(
        *((Command("title", _CoerceText(title)),) if title is not None else ()),
        *((Command("author", _CoerceText(author)),) if author is not None else ()),
        _CreatedOnDef(created_on),
        RenewCommand(
            "maketitle",
            _MaketitleBody(
                resolved,
                global_scale=global_scale,
                main_scale=main_scale,
                abstract=abstract_tex,
                keywords=keywords_tex,
                data_lines=coerced_rows,
            ),
        ),
    )


__all__ = ["TitlePageDefs"]
