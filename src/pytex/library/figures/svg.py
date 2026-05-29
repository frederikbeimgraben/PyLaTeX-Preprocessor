"""SVG inclusion via Inkscape SVG->PDF conversion.

An :class:`SVG` node renders its source (inline ``xml`` or an on-disk ``file``)
to a PDF inside a build directory using ``inkscape`` and then serializes exactly
like :class:`~pytex.IncludeGraphics` pointing at that PDF. Conversion is lazy and
cached: it only runs when the PDF is missing or older than its source.
"""

import hashlib
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import override

from ...model.base_model import Package, TeX
from .graphics import IncludeGraphics


@dataclass(init=False)
class SVG(TeX):
    """Include an SVG, converted to PDF with Inkscape at build time.

    Exactly one of ``xml`` (inline SVG markup) or ``file`` (path to an ``.svg``)
    must be given. ``width``/``height``/``scale``/``angle`` mirror
    :class:`~pytex.IncludeGraphics`. The generated PDF is written to
    ``build_dir`` (created relative to the current working directory, i.e. where
    the build was invoked). ``name`` overrides the output stem.
    """

    xml: str | None
    file: Path | None
    width: str | None
    height: str | None
    scale: float | None
    angle: float | None
    name: str | None
    build_dir: Path
    _rendered: Path | None = field(default=None, compare=False)

    def __init__(
        self,
        xml: str | None = None,
        file: str | Path | None = None,
        *,
        width: str | None = None,
        height: str | None = None,
        scale: float | None = None,
        angle: float | None = None,
        name: str | None = None,
        build_dir: str | Path = "build",
    ) -> None:
        if (xml is None) == (file is None):
            raise ValueError("SVG requires exactly one of 'xml' or 'file'")
        self.xml = xml
        self.file = Path(file) if file is not None else None
        self.width = width
        self.height = height
        self.scale = scale
        self.angle = angle
        self.name = name
        self.build_dir = Path(build_dir)
        self._rendered = None

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return {"graphicx"}

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    def _stem(self) -> str:
        if self.name is not None:
            return self.name
        if self.file is not None:
            return self.file.stem
        digest = hashlib.sha1(self.xml.encode("utf-8")).hexdigest()[:12]  # pyright: ignore[reportOptionalMemberAccess]
        return f"svg-{digest}"

    def _source_path(self) -> Path:
        if self.file is not None:
            return self.file
        src = self.build_dir / f"{self._stem()}.svg"
        if not src.exists() or src.read_text() != self.xml:
            src.write_text(self.xml)  # pyright: ignore[reportArgumentType]
        return src

    def render(self) -> Path:
        """Convert the SVG to PDF (cached) and return the PDF path."""
        if self._rendered is not None:
            return self._rendered

        self.build_dir.mkdir(parents=True, exist_ok=True)
        source = self._source_path()
        pdf = self.build_dir / f"{self._stem()}.pdf"

        fresh = pdf.exists() and pdf.stat().st_mtime >= source.stat().st_mtime
        if not fresh:
            if shutil.which("inkscape") is None:
                raise RuntimeError(
                    "inkscape not found; required to convert SVG to PDF"
                )
            subprocess.run(
                [
                    "inkscape",
                    str(source),
                    "--export-type=pdf",
                    f"--export-filename={pdf}",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

        self._rendered = pdf
        return pdf

    @override
    def serialize(self) -> str:
        pdf = self.render()
        return IncludeGraphics(
            str(pdf),
            width=self.width,
            height=self.height,
            scale=self.scale,
            angle=self.angle,
        ).serialize()
