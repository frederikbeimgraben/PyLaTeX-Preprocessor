"""Tests for the TeX-node tree renderer (`--tree`)."""

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
    # WithPackage wrappers collapse onto the wrapped node, tagged with the
    # package they attach (Cref requires cleveref).
    tree = render_tree(Cref("fig:1"))
    assert "WithPackage" not in tree
    assert r"ControlSequence \cref [+cleveref]" in tree


def test_tree_distinguishes_space_from_empty():
    # A single-space Raw must not render the same as an empty one.
    assert 'Raw " "' in render_tree(Concat(Raw(" "), Raw("x")))


def test_tree_escapes_newlines_in_raw():
    assert r'Raw "\n\n"' in render_tree(Concat(Raw("\n\n"), Raw("x")))


def test_tree_shows_environments_as_environment_nodes():
    # `Itemize` is a Concat(\begin{itemize}, ..., \end{itemize}); the tree
    # collapses that to a single Environment node, hiding the begin/end.
    tree = render_tree(Itemize("a", "b"))
    assert tree.splitlines()[0] == "Environment {itemize}"
    assert r"\begin" not in tree
    assert r"\end" not in tree


def test_tree_color_wraps_ansi_codes():
    plain = render_tree(Section("X"), color=False)
    colored = render_tree(Section("X"), color=True)
    assert "\033[" not in plain
    assert "\033[" in colored
