from pytex_markdown import Markdown


def test_external_url_link_becomes_href():
    out = Markdown("[site](https://example.com)").rendered
    assert r"\href{https://example.com}{site}" in out


def test_mailto_link_becomes_href():
    out = Markdown("[mail](mailto:a@b.com)").rendered
    assert r"\href{mailto:a@b.com}{mail}" in out


def test_autolink_becomes_href():
    out = Markdown("<https://example.com>").rendered
    assert r"\href{https://example.com}{https://example.com}" in out


def test_bare_url_becomes_href():
    out = Markdown("see https://example.com here").rendered
    assert r"\href{https://example.com}{https://example.com}" in out


def test_relative_file_link_drops_dead_target():
    # A repository-relative path has no meaning in a PDF. hyperref would point
    # at a `LICENSE.pdf` file that does not exist. Only the link text stays.
    out = Markdown("[`LICENSE`](LICENSE)").rendered
    assert r"\href" not in out
    assert r"\texttt{LICENSE}" in out


def test_anchor_link_drops_dead_target():
    out = Markdown("[jump](#section)").rendered
    assert r"\href" not in out
    assert "jump" in out
