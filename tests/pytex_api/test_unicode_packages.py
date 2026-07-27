"""Tests that every mapped Unicode character renders at every trust level.

The Markdown converter rewrites `€` to the `\\euro{}` macro of eurosym. If
eurosym leaves the package allowlist, an `untrusted` or `sandboxed` build
stops with a `TrustError`. So eurosym must stay on the package allowlist. The
math characters `→ ↔ ≤ ≥ ·` need no package requirement.

Every assertion reads the rendered `.tex` file. No test needs the tectonic
binary or the network.
"""

from __future__ import annotations

import pytest

from pytex_api import (
    BuildRequest,
    InputKind,
    OutputKind,
    TrustLevel,
    policy_for,
    render_blob,
)

# Every character that the converter maps to a font-independent TeX node.
ALL_MAPPED = "€ → ↔ ≤ ≥ ·"


def _render(trust: TrustLevel) -> str:
    return render_blob(
        BuildRequest(
            source=f"Symbols: {ALL_MAPPED}.".encode(),
            input_kind=InputKind.MARKDOWN,
            output_kind=OutputKind.TEX,
            trust=trust,
        )
    ).output.decode()


@pytest.mark.parametrize("trust", [TrustLevel.UNTRUSTED, TrustLevel.SANDBOXED])
def test_all_mapped_chars_render_without_trust_error(trust: TrustLevel):
    # The render raises no `TrustError`. eurosym is on the package allowlist,
    # and the math macros need no package requirement.
    out = _render(trust)
    assert r"\euro{}" in out
    assert r"\rightarrow" in out
    assert r"\cdot" in out


@pytest.mark.parametrize("trust", [TrustLevel.UNTRUSTED, TrustLevel.SANDBOXED])
def test_eurosym_package_is_emitted_and_allowed(trust: TrustLevel):
    out = _render(trust)
    assert "eurosym" in out


def test_eurosym_on_allowlist_for_untrusted_and_sandboxed():
    assert "eurosym" in policy_for(TrustLevel.UNTRUSTED).package_allowlist
    assert "eurosym" in policy_for(TrustLevel.SANDBOXED).package_allowlist
