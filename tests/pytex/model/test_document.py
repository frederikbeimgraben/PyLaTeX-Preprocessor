from pytex.commands.builtin import Section
from pytex.model.concat import Concat
from pytex.model.document import Document
from pytex.model.math import Align, Mathbb
from pytex.packages import AMSFONTS, AMSMATH


def test_minimal():
    out = Document("hi").rendered
    assert out == r"\documentclass{article}\begin{document}hi\end{document}"


def test_custom_class():
    out = Document("x", document_class="report").rendered
    assert r"\documentclass{report}" in out


def test_class_options():
    out = Document(
        "x", document_class="article", document_class_options={"a4paper"}
    ).rendered
    assert r"\documentclass[a4paper]{article}" in out


def test_packages_collected_from_body():
    out = Document(Align("x=y")).rendered
    assert r"\usepackage{amsmath}" in out


def test_packages_collected_recursive():
    body = Concat(Section("s"), Align("x=y"), Mathbb("R"))
    out = Document(body).rendered
    assert r"\usepackage{amsmath}" in out
    assert r"\usepackage{amsfonts}" in out


def test_packages_via_preamble():
    out = Document("body", preamble=Mathbb("R")).rendered
    assert r"\usepackage{amsfonts}" in out


def test_extra_packages():
    out = Document("body", extra_packages=frozenset({AMSMATH})).rendered
    assert r"\usepackage{amsmath}" in out


def test_packages_property():
    body = Concat(Align("x=y"), Mathbb("R"))
    pkgs = Document(body).packages
    assert AMSMATH in pkgs
    assert AMSFONTS in pkgs
