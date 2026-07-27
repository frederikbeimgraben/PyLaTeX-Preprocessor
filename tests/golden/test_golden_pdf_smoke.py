"""Optional smoke test that one golden sample builds to a PDF.

This is not a golden test. PDF bytes are not deterministic, and a build needs
the tectonic binary. So this test never runs in CI. To run it, install Podman
and set `PYTEX_TEST_PODMAN=1`.

The test builds one sample through the Podman sandbox and checks that the
output starts with `%PDF-`. It compares no hash and no bytes. The `.tex`
goldens in `test_golden` are the real regression guard.

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
    # This warm-up runs once and needs more privileges. It gives the offline
    # `untrusted` build a tectonic cache that matches the tectonic version.
    # The sandbox suite does the same.
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
