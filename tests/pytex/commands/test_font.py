from pytex.commands.font import (
    LARGE,
    Bfseries,
    Fontsize,
    Huge,
    Itshape,
    Large,
    Mdseries,
    Normalfont,
    Rmfamily,
    Scshape,
    Selectfont,
    Sffamily,
    Slshape,
    Ttfamily,
    Upshape,
    footnotesize,
    huge,
    large,
    normalsize,
    scriptsize,
    small,
    tiny,
)


def test_fontsize_two_params():
    assert Fontsize("12pt", "14pt").rendered == r"\fontsize{12pt}{14pt}"


def test_selectfont():
    assert Selectfont().rendered == r"\selectfont"


def test_family_switches():
    assert Rmfamily().rendered == r"\rmfamily"
    assert Sffamily().rendered == r"\sffamily"
    assert Ttfamily().rendered == r"\ttfamily"


def test_series_switches():
    assert Bfseries().rendered == r"\bfseries"
    assert Mdseries().rendered == r"\mdseries"


def test_shape_switches():
    assert Itshape().rendered == r"\itshape"
    assert Slshape().rendered == r"\slshape"
    assert Scshape().rendered == r"\scshape"
    assert Upshape().rendered == r"\upshape"


def test_normalfont():
    assert Normalfont().rendered == r"\normalfont"


def test_size_switches():
    assert tiny().rendered == r"\tiny"
    assert scriptsize().rendered == r"\scriptsize"
    assert footnotesize().rendered == r"\footnotesize"
    assert small().rendered == r"\small"
    assert normalsize().rendered == r"\normalsize"
    assert large().rendered == r"\large"
    assert Large().rendered == r"\Large"
    assert LARGE().rendered == r"\LARGE"
    assert huge().rendered == r"\huge"
    assert Huge().rendered == r"\Huge"


def test_size_switch_names_match_latex_spelling():
    # Each factory uses the LaTeX command spelling as its name, with the same
    # letter case. This rule gives `large`, `Large` and `LARGE` three different
    # registry keys.
    for factory in (large, Large, LARGE, huge, Huge):
        assert factory().rendered == f"\\{factory.__name__}"
