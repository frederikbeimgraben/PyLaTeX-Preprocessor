from pytex_markdown import Markdown


def test_eval_comment_evaluates_python_expression():
    out = Markdown('[//]: # "1 + 2"').rendered
    assert "3" in out


def test_eval_comment_splices_tex_node_result():
    out = Markdown("[//]: # \"Section('Generated')\"").rendered
    assert r"\section{Generated}" in out


def test_eval_comment_uses_registry_namespace():
    out = Markdown("[//]: # \"InfoBox('hi')\"").rendered
    assert "mdframed" in out and "hi" in out


def test_non_comment_link_ref_def_renders_nothing():
    # A real link reference definition (label != "//") stays empty.
    out = Markdown('[ref]: https://example.com "title"').rendered
    assert out.strip() == ""


def test_eval_comment_among_paragraphs():
    out = Markdown('Before.\n\n[//]: # "7*6"\n\nAfter.').rendered
    assert "Before." in out and "After." in out and "42" in out
