"""Tests for the generic listings library."""

from pytex import Bash, InlineCode, Java, Listing, LstDefineStyle, LstSet, Python


class TestListing:
    def test_basic(self):
        out = Listing("print(1)").serialize()
        assert out == "\\begin{lstlisting}\nprint(1)\n\\end{lstlisting}"

    def test_with_options(self):
        out = Listing(
            "x", language="Python", caption="Demo", label="lst:d"
        ).serialize()
        assert "language={Python}" in out
        assert "caption={Demo}" in out
        assert "label={lst:d}" in out

    def test_required_packages(self):
        assert Listing("x").required_packages == {"listings"}

    def test_code_stripped_of_outer_newlines(self):
        out = Listing("\n\ncode\n\n").serialize()
        assert out == "\\begin{lstlisting}\ncode\n\\end{lstlisting}"


class TestLanguages:
    def test_python(self):
        assert "language={Python}" in Python("x").serialize()

    def test_bash_maps_to_bash_token(self):
        assert "language={bash}" in Bash("ls").serialize()

    def test_java(self):
        assert "language={Java}" in Java("x").serialize()


class TestHelpers:
    def test_lstset(self):
        assert LstSet(numbers="left", breaklines=True).serialize() == (
            "\\lstset{numbers={left},breaklines}"
        )

    def test_lstdefinestyle(self):
        out = LstDefineStyle("mystyle", language="C").serialize()
        assert out == "\\lstdefinestyle{mystyle}{language={C}}"

    def test_inline_code(self):
        assert InlineCode("x=1").serialize() == "\\lstinline|x=1|"

    def test_inline_code_picks_alt_delimiter(self):
        assert InlineCode("a|b").serialize() == "\\lstinline!a|b!"
