"""The deprecated `pytex_protocol` package stays as a shim."""

import warnings


def test_pytex_protocol_reexports_public_api():
    import pytex_markdown.protocol as new

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        import pytex_protocol as old

    for name in new.__all__:
        assert getattr(old, name) is getattr(new, name)


def test_pytex_protocol_frontmatter_shim():
    from pytex_markdown.frontmatter import split_frontmatter as new
    from pytex_protocol.frontmatter import split_frontmatter as old

    assert old is new


def test_pytex_protocol_import_warns():
    import importlib

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        importlib.reload(__import__("pytex_protocol"))
    assert any(issubclass(w.category, DeprecationWarning) for w in caught)
