"""Tests for the compile step.

`build_tectonic_cmd` is pure, so most tests only inspect the argv it returns.
The last test runs a real build. pytest skips that test when the tectonic
binary is missing.
"""

import io
import shutil
import tempfile
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
from pytex_api._compile import build_tectonic_cmd, compile_to_pdf
from pytex_api._models import TrustError
from pytex_api._policy import policy_for
from pytex_builder.console import Console


def _cmd(level: TrustLevel) -> list[str]:
    return build_tectonic_cmd(
        Path("tectonic"),
        Path("/work/document.tex"),
        Path("/work/build"),
        policy_for(level),
    )


def test_untrusted_cmd_forces_no_shell_escape_and_only_cached():
    cmd = _cmd(TrustLevel.UNTRUSTED)
    assert "--only-cached" in cmd
    assert "shell-escape" not in cmd


def test_sandboxed_cmd_forces_no_shell_escape_and_only_cached():
    cmd = _cmd(TrustLevel.SANDBOXED)
    assert "--only-cached" in cmd
    assert "shell-escape" not in cmd


def test_trusted_cmd_enables_shell_escape_and_network():
    cmd = _cmd(TrustLevel.TRUSTED)
    assert "--only-cached" not in cmd
    assert "shell-escape" in cmd


def test_cmd_outputs_into_build_dir_and_ends_with_tex():
    cmd = _cmd(TrustLevel.UNTRUSTED)
    assert "--outdir" in cmd
    assert cmd[cmd.index("--outdir") + 1] == "/work/build"
    assert cmd[-1] == "/work/document.tex"


def test_asset_named_document_tex_cannot_overwrite_the_screened_latex():
    req = BuildRequest(
        source=b"ok",
        input_kind=InputKind.TEX,
        output_kind=OutputKind.PDF,
        trust=TrustLevel.UNTRUSTED,
        assets={"document.tex": b"ATTACKER CONTENT"},
    )
    policy = policy_for(TrustLevel.UNTRUSTED)
    workdir = Path(tempfile.mkdtemp())
    console = Console(stream=io.StringIO())
    try:
        with pytest.raises(TrustError):
            compile_to_pdf("BENIGN LATEX", req, policy, workdir, console, req.assets)
        assert (workdir / "document.tex").read_text() == "BENIGN LATEX"
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


@pytest.mark.skipif(
    shutil.which("tectonic") is None,
    reason="tectonic binary not available; PDF compile cannot run",
)
def test_real_pdf_build_produces_pdf_bytes():
    res = render_blob(
        BuildRequest(
            source=b"# Title\n\nHello world.",
            input_kind=InputKind.MARKDOWN,
            output_kind=OutputKind.PDF,
            trust=TrustLevel.TRUSTED,
            limits=BuildLimits(wall_timeout_s=120.0),
        )
    )
    assert res.output_kind is OutputKind.PDF
    assert res.output[:5] == b"%PDF-"
