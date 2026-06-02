from pytex_markdown import Markdown


def test_right_arrow():
    assert r"$\rightarrow$" in Markdown("a -> b").rendered


def test_left_arrow():
    assert r"$\leftarrow$" in Markdown("a <- b").rendered


def test_left_right_arrow():
    assert r"$\leftrightarrow$" in Markdown("a <-> b").rendered


def test_double_right_arrow():
    assert r"$\Rightarrow$" in Markdown("a => b").rendered


def test_double_left_right_arrow():
    assert r"$\Leftrightarrow$" in Markdown("a <=> b").rendered


def test_long_arrows():
    out = Markdown("a --> b <-- c <--> d").rendered
    assert r"$\longrightarrow$" in out
    assert r"$\longleftarrow$" in out
    assert r"$\longleftrightarrow$" in out


def test_longest_match_wins():
    # `<-->` must not be split into `<-` + `->`.
    out = Markdown("a <--> b").rendered
    assert r"$\longleftrightarrow$" in out
    assert r"\leftarrow" not in out


def test_le_operator_not_an_arrow():
    # `<=` overwhelmingly means "less than or equal", not a left arrow.
    out = Markdown("x <= y").rendered
    assert "<=" in out
    assert "arrow" not in out


def test_arrows_left_alone_in_code_span():
    out = Markdown("`a -> b`").rendered
    assert r"\texttt{a -> b}" in out
    assert "rightarrow" not in out


def test_arrows_left_alone_in_code_block():
    out = Markdown("```\na -> b\n```\n").rendered
    assert "a -> b" in out
    assert "rightarrow" not in out
