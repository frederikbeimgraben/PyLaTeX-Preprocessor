"""Tests for `Optimize`: simplify a TeX tree without changing what it renders."""

from pytex.commands.builtin import Section
from pytex.model.comment import Comment
from pytex.model.concat import Concat
from pytex.model.control_sequence import ControlSequence
from pytex.model.empty import Empty
from pytex.model.raw import Raw
from pytex_analyze import Optimize


def _types(node):
    return [type(c).__name__ for c in (node.children or ())]


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


def test_pure_marker_raw_expands_to_native_node():
    # A whole-Raw marker evaluates to a native node, not a Raw.
    out = Optimize(Raw(r"\iffalse{pytex(Frac('1', '2'))}\fi"))
    assert isinstance(out, ControlSequence)
    assert out.name == "frac"
    assert out.rendered == r"\frac{1}{2}"


def test_mixed_text_and_markers_expand_to_concat():
    raw = Raw(r"x = \iffalse{pytex(Frac('a', 'b'))}\fi and \iffalse{pytex(2 ** 3)}\fi.")
    out = Optimize(raw)
    assert out.rendered == raw.rendered
    # Literal text is kept as Raw; the markers became their evaluated nodes.
    kinds = _names(out)
    assert "ControlSequence" in kinds  # \frac
    assert kinds[0] == "Raw" and out.children[0].rendered.startswith("x = ")


def test_marker_expansion_preserves_rendering():
    raw = Raw(r"\iffalse{pytex(3 + 4)}\fi")
    out = Optimize(raw)
    assert out.rendered == raw.rendered == "7"


def test_comment_is_detected():
    out = Optimize(Raw("text\n% a note\nmore"))
    assert any(isinstance(c, Comment) for c in out.children)
    assert out.rendered == "text\n% a note\nmore"


def test_comment_owns_its_newline():
    # The comment node carries the terminating newline; no separate Raw("\n").
    out = Optimize(Raw("% one\n% two\nbody"))
    comments = [c for c in out.children if isinstance(c, Comment)]
    assert [c.text for c in comments] == [" one", " two"]
    assert all(c.rendered.endswith("\n") for c in comments)


def test_unterminated_comment_at_eof_stays_text():
    # No trailing newline -> not turned into a Comment (would add a newline).
    raw = Raw("body % trailing")
    out = Optimize(raw)
    assert not any(isinstance(c, Comment) for c in (out.children or ()))
    assert out.rendered == raw.rendered


def test_escaped_percent_is_not_a_comment():
    raw = Raw(r"50\% off")
    out = Optimize(raw)
    assert not any(isinstance(c, Comment) for c in (out.children or ()))
    assert out.rendered == raw.rendered


def test_display_math_delimiters_become_displaymath():
    raw = Raw(r"see \[ x^2 \] here")
    out = Optimize(raw)
    # \[ ... \] becomes DisplayMath; its boundary whitespace is trimmed (TeX
    # ignores it), so the only change from the original is inside the delimiters.
    assert out.rendered == r"see \[x^2\] here"
    assert _types(out) == ["Raw", "Concat", "Raw"]
    math = out.children[1]
    assert [type(c).__name__ for c in math.children] == [
        "ControlSequence",
        "Raw",
        "ControlSequence",
    ]


def test_inline_paren_math_trims_boundary_whitespace():
    # \( ... \) -> Math, boundary whitespace dropped (math-equivalent).
    assert Optimize(Raw(r"\( y = 1 \)")).rendered == r"\(y = 1\)"


def test_dollar_inline_math_becomes_inlinemath():
    # `$...$` -> InlineMath = Concat(Raw('$'), body, Raw('$')); rendering kept.
    raw = Raw(r"see $x^2$ here")
    out = Optimize(raw)
    assert out.rendered == raw.rendered
    assert _types(out) == ["Raw", "Concat", "Raw"]
    math = out.children[1]
    assert math.children[0].rendered == "$"
    assert math.children[-1].rendered == "$"


def test_dollar_math_with_marker_inside_expands():
    raw = Raw(r"$\iffalse{pytex(Frac('1', '2'))}\fi$")
    out = Optimize(raw)
    assert out.rendered == raw.rendered == r"$\frac{1}{2}$"
