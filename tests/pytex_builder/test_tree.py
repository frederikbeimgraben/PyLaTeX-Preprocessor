"""Tests for the node tree view that `--tree` prints."""

from pytex.commands.builtin import Itemize, Section
from pytex.commands.cleveref import Cref
from pytex.model.concat import Concat
from pytex.model.document import Document
from pytex.model.raw import Raw
from pytex_builder.tree import render_tree


def test_tree_shows_control_sequence_and_parameter():
    tree = render_tree(Section("Intro"))
    lines = tree.splitlines()
    assert lines[0] == r"ControlSequence \section"
    assert "└── Parameter { }" in tree
    assert '└── Raw "Intro"' in tree


def test_tree_uses_box_drawing_connectors():
    tree = render_tree(Concat("a", "b"))
    assert "├── " in tree
    assert "└── " in tree


def test_tree_document_root_descends_preamble_and_body():
    tree = render_tree(Document(body="x"))
    assert tree.splitlines()[0].startswith("Document")
    assert 'Raw "x"' in tree


def test_tree_with_package_shows_package_connected():
    # The tree folds a `WithPackage` wrapper into its child node and tags that
    # node with the package requirement. `Cref` requires cleveref.
    tree = render_tree(Cref("fig:1"))
    assert "WithPackage" not in tree
    assert r"ControlSequence \cref [+cleveref]" in tree


def test_tree_distinguishes_space_from_empty():
    # A `Raw` that holds one space must not look like an empty `Raw`.
    assert 'Raw " "' in render_tree(Concat(Raw(" "), Raw("x")))


def test_tree_escapes_newlines_in_raw():
    assert r'Raw "\n\n"' in render_tree(Concat(Raw("\n\n"), Raw("x")))


def test_tree_shows_environments_as_environment_nodes():
    # `Itemize` is a `Concat` of `\begin{itemize}`, the items, and
    # `\end{itemize}`. The tree shows one `Environment` node instead and hides
    # the two control sequences.
    tree = render_tree(Itemize("a", "b"))
    assert tree.splitlines()[0] == "Environment {itemize}"
    assert r"\begin" not in tree
    assert r"\end" not in tree


def test_tree_shows_math_nodes_by_name():
    from pytex.model.math import DisplayMath, InlineMath, Math

    assert render_tree(DisplayMath("x")).splitlines()[0] == "DisplayMath"
    assert render_tree(Math("x")).splitlines()[0] == "Math"
    assert render_tree(InlineMath("x")).splitlines()[0] == "InlineMath"
    # The tree hides the math delimiters and shows the body under the node.
    assert r"\[" not in render_tree(DisplayMath("x"))


def test_tree_color_wraps_ansi_codes():
    plain = render_tree(Section("X"), color=False)
    colored = render_tree(Section("X"), color=True)
    assert "\033[" not in plain
    assert "\033[" in colored
