import pytest

from pytex_hsrtreport.voting import VotingResults


@pytest.mark.parametrize(
    "yes,no,expected",
    [
        (10, 3, "britishracinggreen"),
        (3, 10, "red"),
        (5, 5, "eggplant"),
        (1, 0, "britishracinggreen"),
        (0, 1, "red"),
        (0, 0, "eggplant"),
    ],
)
def test_color_picked_in_python(yes: int, no: int, expected: str):
    assert VotingResults(yes=yes, no=no, abstain=0).color == expected


def test_renders_with_picked_color():
    out = VotingResults(yes=10, no=3, abstain=2).rendered
    assert "britishracinggreen" in out
    assert "thumbs-up" in out
    assert "thumbs-down" in out
    assert "vote-yea" in out


def test_includes_vote_counts():
    out = VotingResults(yes=7, no=2, abstain=1).rendered
    assert "7" in out and "2" in out and "1" in out
