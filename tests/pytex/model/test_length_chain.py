from pytex.commands.lengths import (
    Baselineskip,
    Fill_len,
    Linewidth,
    Parindent,
    Textwidth,
)
from pytex.model.length import Length
from pytex.packages import CALC


def test_length_plus_length():
    assert (Linewidth() + Textwidth()).rendered == r"\linewidth+\textwidth"


def test_length_minus_length():
    assert (Textwidth() - Linewidth()).rendered == r"\textwidth-\linewidth"


def test_rsub():
    assert ("5cm" - Parindent()).rendered == r"5cm-\parindent"


def test_radd():
    assert ("5cm" + Parindent()).rendered == r"5cm+\parindent"


def test_chain_mixed_ops():
    out = (2 * Textwidth() - Linewidth() + "1cm").rendered
    assert out == r"2\textwidth-\linewidth+1cm"


def test_mul_div_neg_parenthesize_a_compound_operand():
    # Textwidth() - Parindent() is a compound expression (a top-level "-").
    # Multiplying, dividing or negating it must wrap it in parentheses, or
    # the +/- precedence of the wrapped expression silently changes.
    half = Textwidth() - Parindent()
    assert (0.5 * half).rendered == r"0.5*(\textwidth-\parindent)"
    assert (-half).rendered == r"-(\textwidth-\parindent)"
    assert (half / 2).rendered == r"(\textwidth-\parindent)/2"


def test_double_neg():
    negated = -Parindent()
    assert (-negated).rendered == r"--\parindent"


def test_baselineskip_arithmetic():
    out = (3 * Baselineskip()).rendered
    assert out == r"3\baselineskip"


def test_fill_factory():
    assert Fill_len().rendered == r"\fill"


def test_explicit_length_renders_as_is():
    assert Length("0.5\\linewidth").rendered == r"0.5\linewidth"


def test_length_div():
    assert (Textwidth() / 3).rendered == r"\textwidth/3"


def test_atomic_length_does_not_require_calc():
    assert Textwidth().requires is None
    assert (2 * Textwidth()).requires is None
    assert (-Textwidth()).requires is None


def test_compound_length_requires_calc():
    # +, - and / use calc's infix syntax, so a Length built with one of them
    # must report calc, or Setlength renders an expression the document
    # never loads the package for.
    assert (Textwidth() - Parindent()).requires == frozenset({CALC})
    assert (Linewidth() + "1cm").requires == frozenset({CALC})
    assert (Linewidth() / 2).requires == frozenset({CALC})


def test_setlength_accepts_length():
    from pytex.commands.lengths import Setlength

    out = Setlength(r"\mylen", Linewidth() / 2).rendered
    assert out == r"\setlength{\mylen}{\linewidth/2}"


def test_addtolength_accepts_length():
    from pytex.commands.lengths import Addtolength

    out = Addtolength(r"\mylen", Textwidth() * 2).rendered
    assert "2\\textwidth" in out
