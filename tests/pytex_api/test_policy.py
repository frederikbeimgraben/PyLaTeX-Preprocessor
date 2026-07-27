"""Tests for the capabilities that the trust policy gives to each trust level."""

from pytex_api import TrustLevel, policy_for


def test_untrusted_locks_everything_down():
    p = policy_for(TrustLevel.UNTRUSTED)
    assert not p.allow_python_exec
    assert not p.allow_markdown_eval
    assert not p.allow_tex_replacements
    assert not p.allow_shell_escape
    assert not p.allow_network
    assert p.enforce_package_allowlist
    assert p.apply_rlimits


def test_sandboxed_still_blocks_code_and_shell_but_widens_packages():
    p = policy_for(TrustLevel.SANDBOXED)
    assert not p.allow_python_exec
    assert not p.allow_markdown_eval
    assert not p.allow_tex_replacements
    assert not p.allow_shell_escape
    assert not p.allow_network
    assert p.enforce_package_allowlist
    assert policy_for(TrustLevel.UNTRUSTED).package_allowlist < p.package_allowlist


def test_eurosym_allowlisted_so_euro_glyph_renders_untrusted():
    # The Markdown converter rewrites `€` to the `\euro{}` macro of eurosym.
    # A non-trusted build refuses a document that needs a package outside the
    # package allowlist. So eurosym must stay on the package allowlist.
    for level in (TrustLevel.UNTRUSTED, TrustLevel.SANDBOXED):
        assert "eurosym" in policy_for(level).package_allowlist


def test_trusted_unlocks_everything():
    p = policy_for(TrustLevel.TRUSTED)
    assert p.allow_python_exec
    assert p.allow_markdown_eval
    assert p.allow_tex_replacements
    assert p.allow_shell_escape
    assert p.allow_network
    assert not p.enforce_package_allowlist
    assert not p.apply_rlimits
