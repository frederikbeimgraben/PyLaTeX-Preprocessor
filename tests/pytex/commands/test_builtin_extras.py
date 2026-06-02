from pytex.commands.builtin import (
    BeginAccSupp,
    Blenderfont,
    ChapterStar,
    Dinfont,
    EndAccSupp,
    Foreach,
    Immediate,
    Newglossarystyle,
    Pagenumbering,
    PartStar,
    Rule,
    SectionStar,
    SubsectionStar,
    SubsubsectionStar,
    Verbatiminput,
    Whiledo,
    Write18,
)


def test_rule():
    assert Rule(r"\textwidth", "0.5mm").rendered == r"\rule{\textwidth}{0.5mm}"


def test_pagenumbering():
    assert Pagenumbering("arabic").rendered == r"\pagenumbering{arabic}"
    assert Pagenumbering("roman").rendered == r"\pagenumbering{roman}"


def test_immediate():
    out = Immediate("body").rendered
    assert out.startswith(r"\immediate")
    assert "body" in out


def test_write18():
    out = Write18("texcount").rendered
    assert out == r"\write18{texcount}"


def test_verbatiminput():
    assert Verbatiminput("file.txt").rendered == r"\verbatiminput{file.txt}"


def test_whiledo():
    out = Whiledo(r"\theit<10", "body").rendered
    assert out == r"\whiledo{\theit<10}{body}"


def test_foreach():
    out = Foreach(r"\i", "0,...,5", "body").rendered
    assert r"\foreach \i in {0,...,5}" in out
    assert "{body}" in out


def test_beginaccsupp_with_options():
    out = BeginAccSupp({"ActualText": ""}).rendered
    assert r"\BeginAccSupp{" in out
    assert "ActualText=" in out


def test_endaccsupp():
    assert EndAccSupp().rendered == r"\EndAccSupp"


def test_newglossarystyle():
    out = Newglossarystyle("mystyle", "body").rendered
    assert out == r"\newglossarystyle{mystyle}{body}"


def test_blenderfont():
    assert Blenderfont().rendered == r"\blenderfont"


def test_dinfont():
    assert Dinfont().rendered == r"\dinfont"


def test_part_star():
    assert PartStar("Intro").rendered == r"\part*{Intro}"


def test_chapter_star():
    assert ChapterStar("Intro").rendered == r"\chapter*{Intro}"


def test_section_star():
    assert SectionStar("Intro").rendered == r"\section*{Intro}"


def test_subsection_star():
    assert SubsectionStar("Intro").rendered == r"\subsection*{Intro}"


def test_subsubsection_star():
    assert SubsubsectionStar("Intro").rendered == r"\subsubsection*{Intro}"
