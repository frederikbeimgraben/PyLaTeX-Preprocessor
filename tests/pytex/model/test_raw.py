from pytex.model.raw import Raw


def test_plain_content():
    assert Raw("hello").rendered == "hello"


def test_empty():
    assert Raw("").rendered == ""


def test_eval_simple_expr():
    assert Raw(r"\iffalse{ pytex(1+2) }\fi").rendered == "3"


def test_eval_with_surrounding_text():
    out = Raw(r"a=\iffalse{ pytex(40+2) }\fi end").rendered
    assert out == "a=42 end"


def test_eval_multiple_substitutions():
    out = Raw(
        r"\iffalse{ pytex(1) }\fi-\iffalse{ pytex(2) }\fi-\iffalse{ pytex(3) }\fi"
    ).rendered
    assert out == "1-2-3"


def test_eval_nested_parens():
    out = Raw(r"\iffalse{ pytex((1+2)*(3+4)) }\fi").rendered
    assert out == "21"


def test_eval_calls_registry():
    out = Raw(r"\iffalse{ pytex(Textbf('x')) }\fi").rendered
    assert out == r"\textbf{x}"


def test_eval_extra_namespace():
    out = Raw(r"\iffalse{ pytex(v*2) }\fi", namespace={"v": 21}).rendered
    assert out == "42"


def test_extra_namespace_shadows_registry():
    out = Raw(r"\iffalse{ pytex(Frac) }\fi", namespace={"Frac": "OVERRIDE"}).rendered
    assert out == "OVERRIDE"


def test_eval_unterminated_leaves_content_unchanged():
    content = r"\iffalse{ pytex(1+2 "
    assert Raw(content).rendered == content


def test_no_iffalse_skip_eval():
    content = r"\not iffalse{ pytex(1) } stays"
    assert Raw(content).rendered == content


def test_namespace_default_none():
    r = Raw("hi")
    assert r.namespace is None


def test_allow_replacements_default_true():
    assert Raw("x").allow_replacements is True


def test_allow_replacements_false_skips_eval():
    content = r"\iffalse{ pytex(1+2) }\fi"
    r = Raw(content, allow_replacements=False)
    assert r.rendered == content


def test_allow_replacements_false_with_namespace():
    content = r"\iffalse{ pytex(v) }\fi"
    r = Raw(content, namespace={"v": 99}, allow_replacements=False)
    assert r.rendered == content
