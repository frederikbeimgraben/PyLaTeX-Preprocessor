from pytex.commands.definitions import (
    DeclareRobustCommandStar,
    NewcommandStar,
    ProvidecommandStar,
    RenewcommandStar,
)


def test_newcommand_star():
    assert NewcommandStar(r"\foo", "hi").rendered == r"\newcommand*{\foo}{hi}"


def test_renewcommand_star():
    assert RenewcommandStar(r"\foo", "hi").rendered == r"\renewcommand*{\foo}{hi}"


def test_providecommand_star():
    assert ProvidecommandStar(r"\foo", "hi").rendered == r"\providecommand*{\foo}{hi}"


def test_declarerobustcommand_star():
    assert (
        DeclareRobustCommandStar(r"\foo", "hi").rendered
        == r"\DeclareRobustCommand*{\foo}{hi}"
    )


def test_newcommand_star_with_args():
    out = NewcommandStar(r"\foo", "hi", nargs=2, default="d").rendered
    assert out == r"\newcommand*{\foo}[2][d]{hi}"
