import hashlib
import subprocess
from pathlib import Path

import pytest

from pytex.model.image import IncludeImage


def test_pdf_extension_resolves_to_source(tmp_path):
    src = tmp_path / "x.pdf"
    src.write_bytes(b"%PDF")
    img = IncludeImage(src)
    assert img.resolved_path == src


def test_png_extension_resolves_to_source(tmp_path):
    src = tmp_path / "x.png"
    src.write_bytes(b"\x89PNG")
    img = IncludeImage(src)
    assert img.resolved_path == src


def test_jpg_extension_resolves_to_source(tmp_path):
    src = tmp_path / "x.jpg"
    src.write_bytes(b"\xff\xd8")
    img = IncludeImage(src)
    assert img.resolved_path == src


def test_svg_extension_routes_through_build(tmp_path):
    src = tmp_path / "x.svg"
    src.write_text("<svg></svg>")
    img = IncludeImage(src)
    target = img.resolved_path
    assert target.parts[0] == "build"
    assert target.suffix == ".pdf"
    assert "x-" in target.name


def test_svg_target_uses_content_sha_digest(tmp_path):
    src = tmp_path / "logo.svg"
    content = "<svg></svg>"
    src.write_text(content)
    img = IncludeImage(src)
    expected_prefix = hashlib.sha1(content.encode()).hexdigest()[:10]
    assert expected_prefix in img.resolved_path.name


def test_svg_target_changes_when_content_changes(tmp_path):
    # The path does not change when you edit the source. The digest must
    # change, or PyTeX reuses a stale PDF.
    src = tmp_path / "logo.svg"
    src.write_text("<svg>old</svg>")
    before = IncludeImage(src).resolved_path.name
    src.write_text("<svg>new</svg>")
    after = IncludeImage(src).resolved_path.name
    assert before != after


def test_ensure_converted_invokes_inkscape(monkeypatch, tmp_path):
    src = tmp_path / "x.svg"
    src.write_text("<svg>invoke</svg>")
    img = IncludeImage(src)
    # The content-addressed cache target lives in the literal `build`
    # directory. Delete a leftover file from an earlier run, so this test
    # runs the conversion.
    img.resolved_path.unlink(missing_ok=True)
    calls: list[list[str]] = []

    def fake_run(cmd, check, capture_output):
        calls.append(cmd)
        Path(cmd[-1].split("=", 1)[1]).write_bytes(b"%PDF-mock")

        class R:
            returncode = 0

        return R()

    monkeypatch.setattr(subprocess, "run", fake_run)
    img.ensure_converted()
    assert any("inkscape" in c[0] for c in calls)
    assert img.resolved_path.exists()
    img.resolved_path.unlink(missing_ok=True)


def test_ensure_converted_skips_if_target_exists(monkeypatch, tmp_path):
    src = tmp_path / "x.svg"
    src.write_text("<svg></svg>")
    img = IncludeImage(src)
    img.resolved_path.parent.mkdir(parents=True, exist_ok=True)
    img.resolved_path.write_bytes(b"%PDF-already")

    called = []
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: called.append(a))
    img.ensure_converted()
    assert called == []


def test_pdf_compat_skips_conversion(tmp_path, monkeypatch):
    src = tmp_path / "x.pdf"
    src.write_bytes(b"%PDF")
    img = IncludeImage(src)
    called = []
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: called.append(a))
    img.ensure_converted()
    assert called == []


def test_read_bytes_returns_resolved_contents(tmp_path):
    src = tmp_path / "x.pdf"
    src.write_bytes(b"%PDF-DATA")
    img = IncludeImage(src)
    assert img.read_bytes() == b"%PDF-DATA"


def test_base64_payload_is_valid_b64(tmp_path):
    import base64

    src = tmp_path / "x.pdf"
    src.write_bytes(b"hello world")
    img = IncludeImage(src)
    payload = img.base64_payload()
    assert base64.b64decode(payload) == b"hello world"


def test_unsupported_ext_raises(tmp_path):
    src = tmp_path / "x.bmp"
    src.write_bytes(b"BM")
    img = IncludeImage(src)
    with pytest.raises(ValueError):
        _ = img.resolved_path
