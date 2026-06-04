"""Optional "does it build at all" smoke for the golden samples.

This is deliberately *not* a golden test: PDF bytes are non-deterministic and a
build needs tectonic, so it never runs in CI. It is opt-in (set
``PYTEX_TEST_PODMAN=1`` with podman installed) and only asserts that a sample
compiles to a ``%PDF-`` blob through the sandboxed build path -- no hash, no byte
comparison. The deterministic ``.tex`` goldens in :mod:`test_golden` are the
actual regression guard.

    PYTEX_TEST_PODMAN=1 pytest tests/golden/test_golden_pdf_smoke.py -q
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from pytex_api import (
    BuildLimits,
    BuildRequest,
    InputKind,
    OutputKind,
    TrustLevel,
    render_blob,
)
from pytex_api._sandbox import (
    build_sandbox_image,
    podman_available,
    sandbox_image_present,
    warm_sandbox_cache,
)

_INPUTS = Path(__file__).resolve().parent / "inputs"


@pytest.mark.skipif(
    not (podman_available() and os.environ.get("PYTEX_TEST_PODMAN")),
    reason="set PYTEX_TEST_PODMAN=1 with podman installed to run the live build",
)
def test_plain_sample_builds_pdf() -> None:
    # One-time privileged warm-up so the offline untrusted build gets a
    # version-matched tectonic cache hit (mirrors the sandbox suite).
    if not sandbox_image_present():
        build_sandbox_image()
    warm_sandbox_cache()

    source = (_INPUTS / "plain.md").read_bytes()
    result = render_blob(
        BuildRequest(
            source=source,
            input_kind=InputKind.MARKDOWN,
            output_kind=OutputKind.PDF,
            trust=TrustLevel.UNTRUSTED,
            limits=BuildLimits(wall_timeout_s=300.0),
        )
    )
    assert result.output_kind is OutputKind.PDF
    assert result.output[:5] == b"%PDF-"
