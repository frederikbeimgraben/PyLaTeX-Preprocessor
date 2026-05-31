from pytex.commands.font import (
    Bfseries,
    Fontsize,
    Footnotesize,
    Huge,
    HugeBig,
    Itshape,
    Large,
    LargeBig,
    LargeMid,
    Mdseries,
    Normalfont,
    Normalsize,
    Rmfamily,
    Scriptsize,
    Scshape,
    Selectfont,
    Sffamily,
    Slshape,
    Small,
    Tiny,
    Ttfamily,
    Upshape,
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
    assert Tiny().rendered == r"\tiny"
    assert Scriptsize().rendered == r"\scriptsize"
    assert Footnotesize().rendered == r"\footnotesize"
    assert Small().rendered == r"\small"
    assert Normalsize().rendered == r"\normalsize"
    assert Large().rendered == r"\large"
    assert LargeMid().rendered == r"\Large"
    assert LargeBig().rendered == r"\LARGE"
    assert Huge().rendered == r"\huge"
    assert HugeBig().rendered == r"\Huge"
