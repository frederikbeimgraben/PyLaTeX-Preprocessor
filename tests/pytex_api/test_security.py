"""Unit tests for the security helpers of `pytex_api`."""

import pytest

from pytex_api import DANGEROUS_PACKAGES, PACKAGE_ALLOWLIST
from pytex_api._models import BuildLimits, TrustError, TrustLevel
from pytex_api._policy import policy_for
from pytex_api._security import (
    enforce_packages,
    extract_packages,
    make_rlimit_preexec,
    strip_markdown_eval_comments,
    truncate_log,
    validate_asset_name,
)

# -- asset name validation -------------------------------------------------


@pytest.mark.parametrize("name", ["logo.png", "fig1.pdf", "a.b.c.jpg", "x"])
def test_valid_asset_names_pass(name):
    assert validate_asset_name(name) == name


@pytest.mark.parametrize(
    "name",
    [
        "/etc/passwd",
        "../escape.png",
        "sub/dir.png",
        "a\\b.png",
        "..",
        ".",
        "",
        "C:evil.png",
        "nul\x00.png",
    ],
)
def test_unsafe_asset_names_rejected(name):
    with pytest.raises(TrustError):
        validate_asset_name(name)


# -- strip the Markdown eval comments --------------------------------------


def test_strip_removes_eval_comment_lines():
    text = "# Title\n\n[//]: # \"Raw('X')\"\n\nbody\n"
    out = strip_markdown_eval_comments(text)
    assert "[//]" not in out
    assert "body" in out


def test_strip_keeps_ordinary_links():
    text = "see [docs](https://example.com) and more\n"
    assert strip_markdown_eval_comments(text) == text


# -- the package allowlist check --------------------------------------------


def test_extract_packages_handles_options_and_lists():
    latex = r"\usepackage[utf8]{inputenc}\RequirePackage{amsmath,amssymb}"
    assert extract_packages(latex) == {"inputenc", "amsmath", "amssymb"}


def test_dangerous_package_rejected_for_untrusted():
    policy = policy_for(TrustLevel.UNTRUSTED)
    with pytest.raises(TrustError, match="code-execution"):
        enforce_packages(r"\usepackage{minted}", policy)


def test_non_allowlisted_package_rejected_for_untrusted():
    policy = policy_for(TrustLevel.UNTRUSTED)
    with pytest.raises(TrustError, match="allowlist"):
        enforce_packages(r"\usepackage{some-exotic-pkg}", policy)


def test_allowlisted_package_accepted_for_untrusted():
    policy = policy_for(TrustLevel.UNTRUSTED)
    enforce_packages(r"\usepackage{amsmath}\usepackage{graphicx}", policy)  # no error


def test_trusted_skips_package_checks():
    policy = policy_for(TrustLevel.TRUSTED)
    enforce_packages(r"\usepackage{minted}\usepackage{anything}", policy)  # no error


def test_dangerous_and_allowlist_are_disjoint():
    assert not (DANGEROUS_PACKAGES & PACKAGE_ALLOWLIST)


# -- log truncation and resource limits -------------------------------------


def test_truncate_log_caps_length():
    limits = BuildLimits(max_log_chars=10)
    out = truncate_log("x" * 100, limits)
    assert out.startswith("x" * 10)
    assert "truncated" in out


def test_truncate_log_short_unchanged():
    limits = BuildLimits(max_log_chars=10)
    assert truncate_log("short", limits) == "short"


def test_rlimit_preexec_is_callable_on_posix():
    import os

    preexec = make_rlimit_preexec(BuildLimits())
    if os.name == "posix":
        assert callable(preexec)
    else:  # pragma: no cover - non-POSIX CI
        assert preexec is None
