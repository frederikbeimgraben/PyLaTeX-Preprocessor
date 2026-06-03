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


def test_literal_block_scalar_preserves_newlines_and_indent():
    src = (
        "---\n"
        "bibliography: |\n"
        "  @book{knuth,\n"
        "    author = {Knuth},\n"
        "  }\n"
        "title: T\n"
        "---\n"
        "Body\n"
    )
    meta, body = split_frontmatter(src)
    # Common indent stripped, inner indentation and line breaks kept.
    assert meta["bibliography"] == "@book{knuth,\n  author = {Knuth},\n}\n"
    # The key after the block is still parsed, and the body is untouched.
    assert meta["title"] == "T"
    assert body == "Body"


def test_folded_block_scalar_joins_lines_with_spaces():
    src = "---\nabstract: >\n  one two\n  three\n\n  next para\n---\nx"
    meta, _ = split_frontmatter(src)
    assert meta["abstract"] == "one two three\nnext para\n"


def test_block_scalar_strip_chomping():
    meta, _ = split_frontmatter("---\nb: |-\n  line1\n  line2\n---\nx")
    assert meta["b"] == "line1\nline2"


def test_block_scalar_keep_chomping():
    meta, _ = split_frontmatter("---\nb: |+\n  line1\n\n\n---\nx")
    assert meta["b"] == "line1\n\n"


def test_pipe_prefixed_scalar_is_not_a_block_scalar():
    # A value that merely starts with `|` stays an ordinary scalar.
    meta, _ = split_frontmatter("---\nt: |pipe\n---\nx")
    assert meta["t"] == "|pipe"
