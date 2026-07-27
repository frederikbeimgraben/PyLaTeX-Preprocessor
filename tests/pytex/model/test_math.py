from pytex.helpers.with_package import WithPackage
from pytex.model.math import (
    Align,
    AlignStar,
    Binom,
    Bmatrix,
    Cases,
    Dfrac,
    DisplayMath,
    Eqref,
    Equation,
    Frac,
    Gather,
    Int,
    Math,
    Mathbb,
    Mathcal,
    Mathfrak,
    Matrix,
    Multline,
    Pmatrix,
    Prod,
    Sqrt,
    Sub,
    SubSuper,
    Sum,
    Super,
    Text,
    Vec,
)
from pytex.packages import AMSFONTS, AMSMATH


def test_math_inline():
    assert Math("x").rendered == r"\(x\)"


def test_display_math():
    assert DisplayMath("x").rendered == r"\[x\]"


def test_math_strips_outer_whitespace():
    # TeX math ignores space at the start and at the end. `Math` and
    # `DisplayMath` remove that space and keep the space inside.
    assert DisplayMath("  x = 1 \n").rendered == r"\[x = 1\]"
    assert Math("  y  ").rendered == r"\(y\)"
    assert DisplayMath("a + b").rendered == r"\[a + b\]"


def test_display_math_drops_blank_lines_at_boundary():
    # A blank line at the start or at the end becomes a `\par` inside math.
    # A `\par` inside math is a hard LaTeX error.
    assert DisplayMath("\n\n x \n\n").rendered == r"\[x\]"


def test_math_trims_concat_boundary_only():
    from pytex.model.concat import Concat
    from pytex.model.math import Frac

    out = DisplayMath(Concat("  x = ", Frac("-b", "2a"), "  "))
    assert out.rendered == r"\[x = \frac{-b}{2a}\]"


def test_equation():
    assert Equation("E=mc^2").rendered == r"\begin{equation}E=mc^2\end{equation}"


def test_align_requires_amsmath():
    a = Align("x=y")
    assert isinstance(a, WithPackage)
    assert AMSMATH in a.requires
    assert a.rendered == r"\begin{align}x=y\end{align}"


def test_align_star_requires_amsmath():
    a = AlignStar("x=y")
    assert AMSMATH in a.requires


def test_gather_requires_amsmath():
    assert AMSMATH in Gather("x").requires


def test_multline_requires_amsmath():
    assert AMSMATH in Multline("x").requires


def test_cases_requires_amsmath():
    assert AMSMATH in Cases("x").requires


def test_frac_basic():
    assert Frac("1", "2").rendered == r"\frac{1}{2}"


def test_dfrac_requires_amsmath():
    d = Dfrac("1", "2")
    assert AMSMATH in d.requires
    assert d.rendered == r"\dfrac{1}{2}"


def test_binom_requires_amsmath():
    b = Binom("n", "k")
    assert AMSMATH in b.requires


def test_sqrt_basic():
    assert Sqrt("x").rendered == r"\sqrt{x}"


def test_sqrt_with_root():
    assert Sqrt("x", n="3").rendered == r"\sqrt[3]{x}"


def test_sub():
    assert Sub("x", "i").rendered == "x_{i}"


def test_super():
    assert Super("x", "2").rendered == "x^{2}"


def test_subsuper():
    assert SubSuper("x", "i", "2").rendered == "x_{i}^{2}"


def test_sum():
    assert Sum("i=0", "n").rendered == r"\sum_{i=0}^{n}"


def test_prod():
    assert Prod().rendered == r"\prod"


def test_int():
    assert Int("0", "1").rendered == r"\int_{0}^{1}"


def test_matrix():
    out = Matrix([["1", "2"], ["3", "4"]]).rendered
    assert out == r"\begin{matrix}1 & 2 \\ 3 & 4\end{matrix}"
    assert AMSMATH in Matrix([["1"]]).requires


def test_pmatrix():
    out = Pmatrix([["a", "b"]]).rendered
    assert out == r"\begin{pmatrix}a & b\end{pmatrix}"


def test_bmatrix():
    out = Bmatrix([["a"]]).rendered
    assert out == r"\begin{bmatrix}a\end{bmatrix}"


def test_mathbb_requires_amsfonts():
    m = Mathbb("R")
    assert AMSFONTS in m.requires
    assert m.rendered == r"\mathbb{R}"


def test_mathfrak_requires_amsfonts():
    assert AMSFONTS in Mathfrak("g").requires


def test_mathcal_no_package():
    assert Mathcal("X").rendered == r"\mathcal{X}"


def test_text_requires_amsmath():
    t = Text("hello")
    assert AMSMATH in t.requires
    assert t.rendered == r"\text{hello}"


def test_eqref_requires_amsmath():
    e = Eqref("eq:x")
    assert AMSMATH in e.requires
    assert e.rendered == r"\eqref{eq:x}"


def test_vec():
    assert Vec("v").rendered == r"\vec{v}"
