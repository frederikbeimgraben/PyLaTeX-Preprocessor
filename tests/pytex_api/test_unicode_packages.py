"""Mapped Unicode chars render under every trust level.

The Markdown converter rewrites ``€`` to eurosym's ``\\euro{}``; eurosym must
therefore be on the package allowlist or an UNTRUSTED/SANDBOXED build would be
refused with a ``TrustError``. The math targets (``→ ↔ ≤ ≥ ·``) pull no package.
All assertions are on the rendered ``.tex`` (OutputKind.TEX), so no tectonic
binary and no network are involved.
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

# Every char the converter maps to a font-independent node.
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
    # No TrustError: eurosym is allowlisted, the math macros need no package.
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
