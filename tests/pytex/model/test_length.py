from pytex.commands.lengths import (
    Baselineskip,
    Linewidth,
    Parindent,
    Textwidth,
)
from pytex.model.length import Length


def test_length_rendered():
    assert Length("0.5cm").rendered == "0.5cm"


def test_textwidth_factory():
    assert Textwidth().rendered == r"\textwidth"


def test_linewidth_factory():
    assert Linewidth().rendered == r"\linewidth"


def test_add():
    assert (Linewidth() + "0.5cm").rendered == r"\linewidth+0.5cm"


def test_sub():
    assert (Textwidth() - "30mm").rendered == r"\textwidth-30mm"


def test_mul_scalar():
    assert (0.5 * Textwidth()).rendered == r"0.5\textwidth"


def test_mul_scalar_right():
    assert (Textwidth() * 2).rendered == r"2\textwidth"


def test_div():
    assert (Textwidth() / 2).rendered == r"\textwidth/2"


def test_neg():
    assert (-Parindent()).rendered == r"-\parindent"


def test_chain():
    out = (0.5 * Linewidth() - Parindent()).rendered
    assert out == r"0.5\linewidth-\parindent"


def test_baselineskip():
    assert (Baselineskip() * 2).rendered == r"2\baselineskip"
