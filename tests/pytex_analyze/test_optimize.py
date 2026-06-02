"""Tests for `Optimize`: simplify a TeX tree without changing what it renders."""

from pytex.commands.builtin import Section
from pytex.model.concat import Concat
from pytex.model.control_sequence import ControlSequence
from pytex.model.empty import Empty
from pytex.model.raw import Raw
from pytex_analyze import Optimize


def _names(node):
    """Class names of a node's direct children."""
    return [type(c).__name__ for c in (node.children or ())]


def test_render_is_preserved_for_bare_command():
    raw = Raw(r"\newpage")
    out = Optimize(raw)
    assert out.rendered == raw.rendered


def test_bare_command_becomes_control_sequence():
    out = Optimize(Raw(r"\clearpage"))
    assert isinstance(out, ControlSequence)
    assert out.name == "clearpage"


def test_single_arg_command_becomes_control_sequence():
    out = Optimize(Raw(r"\section{Intro}"))
    assert isinstance(out, ControlSequence)
    assert out.name == "section"
    assert out.rendered == r"\section{Intro}"


def test_environment_raw_becomes_environment_nodes():
    out = Optimize(Raw(r"\begin{center}hi\end{center}"))
    # Environment is Concat(\begin{center}, body, \end{center}).
    assert isinstance(out, Concat)
    assert _names(out)[0] == "ControlSequence"
    assert out.rendered == r"\begin{center}hi\end{center}"


def test_plain_text_raw_is_untouched():
    raw = Raw("just some text")
    assert Optimize(raw) is raw


def test_nested_concats_are_flattened():
    nested = Concat("a", Concat("b", Concat("c", "d")))
    out = Optimize(nested)
    assert isinstance(out, Concat)
    # Flattened to four Raw children, not nested Concats.
    assert _names(out) == ["Raw", "Raw", "Raw", "Raw"]
    assert out.rendered == "abcd"


def test_empty_children_dropped_and_meaning_kept():
    out = Optimize(Concat("a", Empty, Raw(""), "b"))
    assert [c.rendered for c in out.children] == ["a", "b"]


def test_whitespace_raw_is_kept():
    out = Optimize(Concat(Raw("a"), Raw(" "), Raw("b")))
    assert out.rendered == "a b"


def test_optimize_preserves_rendering_of_real_document():
    doc = Section("Title")  # ControlSequence with a Parameter subtree
    assert Optimize(doc).rendered == doc.rendered


def test_marker_raw_is_not_misconverted():
    # A Raw carrying a pytex(...) replacement must not be reinterpreted as a
    # literal command (its rendered form differs from its content).
    raw = Raw(r"\iffalse{pytex(3 + 4)}\fi")
    out = Optimize(raw)
    assert out.rendered == raw.rendered == "7"
