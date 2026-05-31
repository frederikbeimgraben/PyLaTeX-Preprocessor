from pytex.commands.floats import Columnbreak, Multicols, Titlepage


def test_multicols_renders_env():
    out = Multicols(3, "body").rendered
    assert out == r"\begin{multicols}{3}body\end{multicols}"


def test_multicols_two():
    out = Multicols(2, "x").rendered
    assert "{multicols}{2}" in out


def test_columnbreak():
    assert Columnbreak().rendered == r"\columnbreak"


def test_titlepage_env():
    out = Titlepage("body").rendered
    assert out == r"\begin{titlepage}body\end{titlepage}"
