from pytex.commands.lengths import (
    Baselineskip,
    Fill,
    Linewidth,
    Parindent,
    Textwidth,
)
from pytex.model.length import Length


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


def test_double_neg():
    assert (-(-Parindent())).rendered == r"--\parindent"


def test_baselineskip_arithmetic():
    out = (3 * Baselineskip()).rendered
    assert out == r"3\baselineskip"


def test_fill_factory():
    assert Fill().rendered == r"\fill"


def test_explicit_length_renders_as_is():
    assert Length("0.5\\linewidth").rendered == r"0.5\linewidth"


def test_length_div():
    assert (Textwidth() / 3).rendered == r"\textwidth/3"


def test_setlength_accepts_length():
    from pytex.commands.lengths import Setlength

    out = Setlength(r"\mylen", Linewidth() / 2).rendered
    assert out == r"\setlength{\mylen}{\linewidth/2}"


def test_addtolength_accepts_length():
    from pytex.commands.lengths import Addtolength

    out = Addtolength(r"\mylen", Textwidth() * 2).rendered
    assert "2\\textwidth" in out
