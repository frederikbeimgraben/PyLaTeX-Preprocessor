from pytex.model.package import Package
from pytex.packages import (
    AMSFONTS,
    AMSMATH,
    GRAPHICX,
    HYPERREF,
    PGF,
    SCRLAYER_SCRPAGE,
    TIKZ,
    TYPEAREA,
    Packages,
)


def test_constants_are_packages():
    for p in (
        AMSMATH,
        AMSFONTS,
        GRAPHICX,
        HYPERREF,
        TIKZ,
        PGF,
        TYPEAREA,
        SCRLAYER_SCRPAGE,
    ):
        assert isinstance(p, Package)


def test_constants_match_enum():
    assert Packages.AMSMATH.value is AMSMATH
    assert Packages.TIKZ.value is TIKZ


def test_package_names_correct():
    assert AMSMATH.name == "amsmath"
    assert TIKZ.name == "tikz"
    assert SCRLAYER_SCRPAGE.name == "scrlayer-scrpage"


def test_cleveref_depends_on_hyperref():
    from pytex.packages import CLEVEREF, HYPERREF

    assert HYPERREF in CLEVEREF.after
