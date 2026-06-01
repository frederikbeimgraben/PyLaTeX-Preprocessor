from pytex.commands.biblatex import (
    Addbibresource,
    Autocite,
    Citeauthor,
    Footcite,
    Parencite,
    Printbibliography,
    Textcite,
)
from pytex.commands.captions import Caption, Captionof, Captionsetup, Subcaption
from pytex.commands.cleveref import Cref, Crefformat, Crefname, CrefnameUpper, CrefUpper
from pytex.commands.colors import (
    Colorbox,
    Definecolor,
    Fcolorbox,
    Pagecolor,
    SelectColor,
    Textcolor,
)
from pytex.commands.conditionals import (
    Apptocmd,
    Equal,
    Ifdefstring,
    Ifstrequal,
    Ifthenelse,
    Pretocmd,
)
from pytex.commands.counters import (
    Addtocounter,
    Alph,
    Arabic,
    Newcounter,
    RomanCounter,
    Setcounter,
    Stepcounter,
    UseCounter,
    Value,
)
from pytex.commands.definitions import (
    DeclareRobustCommand,
    Def,
    Newcommand,
    Newenvironment,
    Providecommand,
    Renewcommand,
    Renewenvironment,
)
from pytex.commands.floats import (
    Figure,
    FigureStar,
    Floatsetup,
    Minipage,
    Newfloat,
    Restylefloat,
    Table,
    TableStar,
)
from pytex.commands.fontawesome import (
    FaCheckCircle,
    FaExclamationTriangle,
    FaIcon,
    FaInfoCircle,
)
from pytex.commands.fontspec import (
    Newfontfamily,
    Setmainfont,
    Setmonofont,
    Setsansfont,
)
from pytex.commands.geometry import Geometry, Newgeometry, Restoregeometry
from pytex.commands.glossaries import (
    Acrfull,
    Acrlong,
    Acrshort,
    Gls,
    Glspl,
    Makeglossaries,
    Newacronym,
    Newglossaryentry,
    Printacronyms,
    Printglossary,
)
from pytex.commands.graphics import (
    Graphicspath,
    Includegraphics,
    Resizebox,
    Rotatebox,
    Scalebox,
)
from pytex.commands.hooks import (
    AtBeginDocument,
    AtBeginEnvironment,
    AtBeginPage,
    AtEndDocument,
    AtEndEnvironment,
    AtEndOfClass,
    AtEndOfPackage,
)
from pytex.commands.hyperref import (
    Autoref,
    Href,
    Hyperlink,
    Hypersetup,
    Hypertarget,
    Nolinkurl,
    Url,
)
from pytex.commands.lengths import (
    Addtolength,
    Newlength,
    Setlength,
    Settodepth,
    Settoheight,
    Settowidth,
)
from pytex.commands.listings import (
    Lstdefinestyle,
    Lstinline,
    Lstinputlisting,
    Lstlisting,
    Lstset,
)
from pytex.commands.mdframed import Mdfdefinestyle, Mdframed, Newmdenv
from pytex.commands.setspace import (
    Doublespacing,
    Onehalfspacing,
    Setstretch,
    Singlespacing,
    Spacing,
)
from pytex.commands.tables import (
    Arraybackslash,
    Bottomrule,
    Cline,
    Cmidrule,
    Hline,
    Longtable,
    Midrule,
    Multicolumn,
    Multirow,
    Newcolumntype,
    Tabular,
    Tabularx,
    Toprule,
)
from pytex.packages import (
    BIBLATEX,
    BOOKTABS,
    CAPTION,
    CLEVEREF,
    ETOOLBOX,
    FONTAWESOME,
    FONTSPEC,
    GEOMETRY,
    GLOSSARIES,
    GRAPHICX,
    HYPERREF,
    IFTHEN,
    LISTINGS,
    LONGTABLE,
    MDFRAMED,
    MULTIROW,
    SETSPACE,
    SUBCAPTION,
    TABULARX,
    XCOLOR,
)


def test_colors_render_and_require_xcolor():
    assert Definecolor("c", "rgb", "0,0,0").rendered == r"\definecolor{c}{rgb}{0,0,0}"
    assert XCOLOR in Definecolor("c", "rgb", "0,0,0").requires
    assert Textcolor("red", "x").rendered == r"\textcolor{red}{x}"
    assert SelectColor("red").rendered == r"\color{red}"
    assert Colorbox("red", "x").rendered == r"\colorbox{red}{x}"
    assert Fcolorbox("red", "blue", "x").rendered == r"\fcolorbox{red}{blue}{x}"
    assert Pagecolor("white").rendered == r"\pagecolor{white}"


def test_includegraphics_options():
    out = Includegraphics(
        "f.png",
        width="5cm",
        height="3cm",
        scale="0.5",
        angle="30",
        keepaspectratio=True,
        extra_options={"trim": "0 0 0 0"},
    ).rendered
    assert "width=5cm" in out and "height=3cm" in out
    assert "scale=0.5" in out and "angle=30" in out
    assert "keepaspectratio" in out and "trim=0 0 0 0" in out
    assert out.endswith("{f.png}")


def test_includegraphics_no_opts():
    assert Includegraphics("f.png").rendered == r"\includegraphics{f.png}"
    assert GRAPHICX in Includegraphics("f.png").requires


def test_graphicspath():
    assert Graphicspath("a/", "b/").rendered == r"\graphicspath{{a/}{b/}}"


def test_resizebox_scalebox_rotatebox():
    assert Resizebox("5cm", "!", "x").rendered == r"\resizebox{5cm}{!}{x}"
    assert Scalebox("0.5", "x").rendered == r"\scalebox{0.5}{x}"
    assert Rotatebox("45", "x").rendered == r"\rotatebox{45}{x}"


def test_hyperref_commands():
    h = Hypersetup({"colorlinks": "true"})
    assert HYPERREF in h.requires
    assert "colorlinks=true" in h.rendered
    assert Href("http://x", "t").rendered == r"\href{http://x}{t}"
    assert Url("http://x").rendered == r"\url{http://x}"
    assert Nolinkurl("x").rendered == r"\nolinkurl{x}"
    assert Hyperlink("n", "t").rendered == r"\hyperlink{n}{t}"
    assert Hypertarget("n", "t").rendered == r"\hypertarget{n}{t}"
    assert Autoref("eq:1").rendered == r"\autoref{eq:1}"


def test_cleveref_commands():
    c = Cref("eq:1", "eq:2")
    assert CLEVEREF in c.requires
    assert c.rendered == r"\cref{eq:1,eq:2}"
    assert CrefUpper("x").rendered == r"\Cref{x}"
    assert (
        Crefname("figure", "Abb", "Abben").rendered == r"\crefname{figure}{Abb}{Abben}"
    )
    assert (
        CrefnameUpper("figure", "Abb", "Abben").rendered
        == r"\Crefname{figure}{Abb}{Abben}"
    )
    assert Crefformat("eq", "(#2#1#3)").rendered == r"\crefformat{eq}{(#2#1#3)}"


def test_biblatex_commands():
    a = Addbibresource("main.bib")
    assert BIBLATEX in a.requires
    assert a.rendered == r"\addbibresource{main.bib}"
    assert Textcite("k1", "k2").rendered == r"\textcite{k1,k2}"
    assert Parencite("k").rendered == r"\parencite{k}"
    assert Autocite("k").rendered == r"\autocite{k}"
    assert Footcite("k").rendered == r"\footcite{k}"
    assert Citeauthor("k").rendered == r"\citeauthor{k}"
    assert Printbibliography().rendered == r"\printbibliography"
    assert "heading=bib" in Printbibliography(heading="bib").rendered


def test_glossaries_commands():
    m = Makeglossaries()
    assert GLOSSARIES in m.requires
    assert m.rendered == r"\makeglossaries"
    assert Newglossaryentry(
        "g1", {"name": "x", "description": "y"}
    ).rendered.startswith(r"\newglossaryentry{g1}{")
    assert (
        Newacronym("h", "HTML", "HyperText").rendered
        == r"\newacronym{h}{HTML}{HyperText}"
    )
    assert Gls("x").rendered == r"\gls{x}"
    assert Glspl("x").rendered == r"\glspl{x}"
    assert Acrshort("x").rendered == r"\acrshort{x}"
    assert Acrlong("x").rendered == r"\acrlong{x}"
    assert Acrfull("x").rendered == r"\acrfull{x}"
    assert Printglossary().rendered == r"\printglossary"
    assert Printacronyms().rendered == r"\printacronyms"


def test_listings_commands():
    s = Lstset({"basicstyle": r"\ttfamily"})
    assert LISTINGS in s.requires
    assert s.rendered == r"\lstset{basicstyle=\ttfamily}"
    assert (
        Lstdefinestyle("my", {"language": "python"}).rendered
        == r"\lstdefinestyle{my}{language=python}"
    )
    inp = Lstinputlisting("f.py", {"language": "python"})
    assert "[language=python]" in inp.rendered and "{f.py}" in inp.rendered
    assert Lstinline("x = 1").rendered == r"\lstinline|x = 1|"
    out = Lstlisting("code", {"language": "python"}).rendered
    assert r"\begin{lstlisting}[language=python]" in out


def test_captions_commands():
    assert Caption("x").rendered == r"\caption{x}"
    assert Caption("Long", short="Short").rendered == r"\caption[Short]{Long}"
    assert Captionof("figure", "x").rendered == r"\captionof{figure}{x}"
    c = Captionsetup({"font": "small"})
    assert CAPTION in c.requires
    sc = Subcaption("x")
    assert SUBCAPTION in sc.requires
    assert sc.rendered == r"\subcaption{x}"


def test_floats():
    assert Figure("x").rendered == r"\begin{figure}x\end{figure}"
    assert r"[htbp]" in Figure("x", placement="htbp").rendered
    assert Table("x").rendered == r"\begin{table}x\end{table}"
    assert FigureStar("x").rendered.startswith(r"\begin{figure*}")
    assert TableStar("x").rendered.startswith(r"\begin{table*}")
    assert Minipage("5cm", "x").rendered == r"\begin{minipage}{5cm}x\end{minipage}"
    assert (
        Minipage("5cm", "x", align="t").rendered
        == r"\begin{minipage}[t]{5cm}x\end{minipage}"
    )
    assert Restylefloat("table").rendered == r"\restylefloat{table}"
    assert Newfloat("foo", "tbp", "lof").rendered == r"\newfloat{foo}{tbp}{lof}"
    assert (
        Floatsetup({"capposition": "top"}).rendered == r"\floatsetup{capposition=top}"
    )


def test_tables_commands():
    assert Tabular("ll", "x").rendered == r"\begin{tabular}{ll}x\end{tabular}"
    t = Tabularx("5cm", "lX", "x")
    assert TABULARX in t.requires
    lt = Longtable("ll", "x")
    assert LONGTABLE in lt.requires
    assert Multicolumn(2, "c", "x").rendered == r"\multicolumn{2}{c}{x}"
    mr = Multirow(2, "*", "x")
    assert MULTIROW in mr.requires
    assert Hline().rendered == r"\hline"
    assert Cline("1-2").rendered == r"\cline{1-2}"
    tr = Toprule()
    assert BOOKTABS in tr.requires
    assert tr.rendered == r"\toprule"
    assert Midrule().rendered == r"\midrule"
    assert Bottomrule().rendered == r"\bottomrule"
    assert Cmidrule("1-3").rendered == r"\cmidrule{1-3}"
    assert Cmidrule("1-3", trim="lr").rendered == r"\cmidrule[lr]{1-3}"
    assert Arraybackslash().rendered == r"\arraybackslash"
    assert (
        Newcolumntype("L", 1, r">{\raggedright}p{#1}").rendered
        == r"\newcolumntype{L}[1]{>{\raggedright}p{#1}}"
    )


def test_setspace_commands():
    s = Setstretch("1.5")
    assert SETSPACE in s.requires
    assert s.rendered == r"\setstretch{1.5}"
    assert Singlespacing().rendered == r"\singlespacing"
    assert Onehalfspacing().rendered == r"\onehalfspacing"
    assert Doublespacing().rendered == r"\doublespacing"
    assert Spacing("1.2", "x").rendered == r"\begin{spacing}{1.2}x\end{spacing}"


def test_fontawesome_commands():
    i = FaIcon("home")
    assert FONTAWESOME in i.requires
    assert i.rendered == r"\faicon{home}"
    assert FaInfoCircle().rendered == r"\faInfoCircle"
    assert FaExclamationTriangle().rendered == r"\faExclamationTriangle"
    assert FaCheckCircle().rendered == r"\faCheckCircle"


def test_fontspec_commands():
    s = Setmainfont("Times")
    assert FONTSPEC in s.requires
    assert s.rendered == r"\setmainfont{Times}"
    assert "Path=fonts/" in Setmainfont("Times", {"Path": "fonts/"}).rendered
    assert Setsansfont("Arial").rendered == r"\setsansfont{Arial}"
    assert Setmonofont("Mono").rendered == r"\setmonofont{Mono}"
    assert Newfontfamily(r"\MyFont", "X").rendered == r"\newfontfamily{\MyFont}{X}"


def test_mdframed_commands():
    m = Mdframed("hi", {"roundcorner": "5pt"})
    assert MDFRAMED in m.requires
    assert m.rendered == r"\begin{mdframed}[roundcorner=5pt]hi\end{mdframed}"
    assert (
        Mdfdefinestyle("s", {"linecolor": "red"}).rendered
        == r"\mdfdefinestyle{s}{linecolor=red}"
    )
    assert (
        Newmdenv("note", {"backgroundcolor": "yellow"}).rendered
        == r"\newmdenv[backgroundcolor=yellow]{note}"
    )


def test_geometry_commands():
    g = Geometry({"top": "2cm", "bottom": "2cm"})
    assert GEOMETRY in g.requires
    out = g.rendered
    assert "top=2cm" in out and "bottom=2cm" in out
    assert Newgeometry({"margin": "1cm"}).rendered.startswith(r"\newgeometry")
    assert Restoregeometry().rendered == r"\restoregeometry"


def test_counters_commands():
    assert Newcounter("c").rendered == r"\newcounter{c}"
    assert Newcounter("c", within="section").rendered == r"\newcounter{c}[section]"
    assert Setcounter("c", 0).rendered == r"\setcounter{c}{0}"
    assert Addtocounter("c", 1).rendered == r"\addtocounter{c}{1}"
    assert Stepcounter("c").rendered == r"\stepcounter{c}"
    assert Value("c").rendered == r"\value{c}"
    assert Arabic("c").rendered == r"\arabic{c}"
    assert RomanCounter("c").rendered == r"\roman{c}"
    assert Alph("c").rendered == r"\alph{c}"
    assert UseCounter("c").rendered == r"\thec"


def test_lengths_commands():
    assert Newlength(r"\mylen").rendered == r"\newlength{\mylen}"
    assert Setlength(r"\mylen", "5pt").rendered == r"\setlength{\mylen}{5pt}"
    assert Addtolength(r"\mylen", "1pt").rendered == r"\addtolength{\mylen}{1pt}"
    assert Settowidth(r"\mylen", "x").rendered == r"\settowidth{\mylen}{x}"
    assert Settoheight(r"\mylen", "x").rendered == r"\settoheight{\mylen}{x}"
    assert Settodepth(r"\mylen", "x").rendered == r"\settodepth{\mylen}{x}"


def test_conditionals_commands():
    i = Ifthenelse("a=b", "yes", "no")
    assert IFTHEN in i.requires
    assert i.rendered == r"\ifthenelse{a=b}{yes}{no}"
    e = Equal("a", "b")
    assert IFTHEN in e.requires
    s = Ifstrequal("a", "b", "y", "n")
    assert ETOOLBOX in s.requires
    Ifdefstring(r"\foo", "bar", "y", "n")
    Pretocmd(r"\section", "pre")
    Apptocmd(r"\section", "post")


def test_hooks_commands():
    assert AtBeginDocument("x").rendered == r"\AtBeginDocument{x}"
    assert AtEndDocument("x").rendered == r"\AtEndDocument{x}"
    be = AtBeginEnvironment("figure", "x")
    assert ETOOLBOX in be.requires
    assert be.rendered == r"\AtBeginEnvironment{figure}{x}"
    assert AtEndEnvironment("figure", "x").rendered == r"\AtEndEnvironment{figure}{x}"
    assert AtBeginPage("x").rendered == r"\AtBeginPage{x}"
    assert AtEndOfPackage("x").rendered == r"\AtEndOfPackage{x}"
    assert AtEndOfClass("x").rendered == r"\AtEndOfClass{x}"


def test_definitions_commands():
    assert Newcommand(r"\foo", "hi").rendered == r"\newcommand{\foo}{hi}"
    assert Newcommand(r"\foo", "hi", nargs=1).rendered == r"\newcommand{\foo}[1]{hi}"
    assert (
        Newcommand(r"\foo", "hi", nargs=1, default="d").rendered
        == r"\newcommand{\foo}[1][d]{hi}"
    )
    assert Renewcommand(r"\foo", "hi").rendered == r"\renewcommand{\foo}{hi}"
    assert Providecommand(r"\foo", "hi").rendered == r"\providecommand{\foo}{hi}"
    assert (
        DeclareRobustCommand(r"\foo", "hi").rendered
        == r"\DeclareRobustCommand{\foo}{hi}"
    )
    assert Newenvironment("foo", "B", "E").rendered == r"\newenvironment{foo}{B}{E}"
    assert (
        Newenvironment("foo", "B", "E", nargs=2).rendered
        == r"\newenvironment{foo}[2]{B}{E}"
    )
    assert Renewenvironment("foo", "B", "E").rendered == r"\renewenvironment{foo}{B}{E}"
    assert Def("foo", "hi").rendered == r"\def\foo{hi}"
