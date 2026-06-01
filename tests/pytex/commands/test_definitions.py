from pytex.commands.definitions import (
    DeclareRobustCommand,
    Newcommand,
    Providecommand,
    Renewcommand,
)


def test_newcommand_star():
    assert Newcommand(r"\foo", "hi", star=True).rendered == r"\newcommand*{\foo}{hi}"


def test_renewcommand_star():
    assert (
        Renewcommand(r"\foo", "hi", star=True).rendered == r"\renewcommand*{\foo}{hi}"
    )


def test_providecommand_star():
    assert (
        Providecommand(r"\foo", "hi", star=True).rendered
        == r"\providecommand*{\foo}{hi}"
    )


def test_declarerobustcommand_star():
    assert (
        DeclareRobustCommand(r"\foo", "hi", star=True).rendered
        == r"\DeclareRobustCommand*{\foo}{hi}"
    )


def test_newcommand_star_with_args():
    out = Newcommand(r"\foo", "hi", nargs=2, default="d", star=True).rendered
    assert out == r"\newcommand*{\foo}[2][d]{hi}"
