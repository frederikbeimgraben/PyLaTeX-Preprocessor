from pytex.model.control_sequence import Parameter
from pytex.model.environment import Begin, End, Environment


def test_begin_no_params():
    assert Begin("center").rendered == r"\begin{center}"


def test_begin_with_params():
    assert Begin("tabular", (Parameter("ll"),)).rendered == r"\begin{tabular}{ll}"


def test_end():
    assert End("center").rendered == r"\end{center}"


def test_environment_basic():
    assert Environment("center", "body").rendered == r"\begin{center}body\end{center}"


def test_environment_with_params():
    out = Environment("tabular", "x", (Parameter("ll"),)).rendered
    assert out == r"\begin{tabular}{ll}x\end{tabular}"


def test_environment_empty_body():
    assert Environment("center", "").rendered == r"\begin{center}\end{center}"
