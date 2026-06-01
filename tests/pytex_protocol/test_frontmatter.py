from pytex_protocol.frontmatter import split_frontmatter


def test_no_frontmatter_returns_text_unchanged():
    meta, body = split_frontmatter("# Title\n\ntext")
    assert meta == {}
    assert body == "# Title\n\ntext"


def test_scalar_and_quote_stripping():
    meta, _ = split_frontmatter('---\ngremium: STUPA\nbeginn: "18:30"\n---\n')
    assert meta["gremium"] == "STUPA"
    assert meta["beginn"] == "18:30"


def test_flow_list():
    meta, _ = split_frontmatter("---\nanwesend: [A, B, C]\n---\n")
    assert meta["anwesend"] == ["A", "B", "C"]


def test_block_list():
    meta, _ = split_frontmatter("---\nentschuldigt:\n  - F. Kurz\n  - G. Lang\n---\n")
    assert meta["entschuldigt"] == ["F. Kurz", "G. Lang"]


def test_body_is_separated_from_frontmatter():
    meta, body = split_frontmatter("---\ngremium: AStA\n---\n\n# Begrüßung\n")
    assert meta["gremium"] == "AStA"
    assert body.strip() == "# Begrüßung"


def test_unterminated_fence_is_not_treated_as_frontmatter():
    text = "---\ngremium: STUPA\nno closing fence\n"
    meta, body = split_frontmatter(text)
    assert meta == {}
    assert body == text
