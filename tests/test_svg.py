"""Tests for the SVG TeX type (Inkscape SVG -> PDF)."""

import shutil
from pathlib import Path

import pytest

from pytex import SVG

_TINY_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">'
    '<rect width="10" height="10" fill="red"/></svg>'
)

_HAS_INKSCAPE = shutil.which("inkscape") is not None


class TestSVGConstruction:
    def test_requires_exactly_one_source(self):
        with pytest.raises(ValueError):
            SVG()
        with pytest.raises(ValueError):
            SVG(xml=_TINY_SVG, file="x.svg")

    def test_required_packages(self):
        assert SVG(xml=_TINY_SVG).required_packages == {"graphicx"}

    def test_stem_from_name(self, tmp_path: Path):
        svg = SVG(xml=_TINY_SVG, name="logo", build_dir=tmp_path)
        assert svg._stem() == "logo"


@pytest.mark.skipif(not _HAS_INKSCAPE, reason="inkscape not installed")
class TestSVGRender:
    def test_render_creates_pdf(self, tmp_path: Path):
        svg = SVG(xml=_TINY_SVG, name="shape", build_dir=tmp_path)
        pdf = svg.render()
        assert pdf.exists()
        assert pdf.suffix == ".pdf"

    def test_serialize_is_includegraphics(self, tmp_path: Path):
        out = SVG(xml=_TINY_SVG, name="shape", width="3cm", build_dir=tmp_path).serialize()
        assert out.startswith("\\includegraphics[width=3cm]{")
        assert out.endswith("shape.pdf}")

    def test_render_is_cached(self, tmp_path: Path):
        svg = SVG(xml=_TINY_SVG, name="shape", build_dir=tmp_path)
        first = svg.render()
        mtime = first.stat().st_mtime
        svg2 = SVG(xml=_TINY_SVG, name="shape", build_dir=tmp_path)
        assert svg2.render().stat().st_mtime == mtime
