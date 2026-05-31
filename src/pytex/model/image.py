import base64
import hashlib
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, override

from ..helpers.parenting import attach
from ..interface.package import PackageProtocol
from ..interface.tex import TeX
from ..registry import Registry

_PDF_COMPAT = {".pdf", ".png", ".jpg", ".jpeg", ".eps"}


def _convert_to_pdf(src: Path, dst: Path) -> None:
    """SVG → PDF via inkscape. Raises FileNotFoundError if inkscape absent."""
    if src.suffix.lower() != ".svg":
        raise ValueError(f"only SVG conversion supported, got {src.suffix}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["inkscape", str(src), "--export-type=pdf", f"--export-filename={dst}"],
        check=True,
        capture_output=True,
    )


@Registry.add
@dataclass
class IncludeImage(TeX):
    """`\\includegraphics{path}` with optional base64 baking.

    - Accepts any image format. SVG is converted to PDF via `inkscape` lazily
      (only when bytes are accessed and `inline_base64=True`).
    - When `inline_base64=True`, `Document` collects the node and emits a
      `\\begin{filecontents*}[overwrite,nosearch]{<resolved>.b64}` block at the
      document start containing the raw base64. A build helper can decode them
      to disk before the TeX run. The `\\includegraphics` line stays unchanged.
    """

    path: Final[str | Path]
    inline_base64: Final[bool] = False
    width: Final[str | None] = None
    height: Final[str | None] = None
    scale: Final[str | None] = None
    keepaspectratio: Final[bool] = False
    _parent: "TeX | None" = field(default=None, init=False, compare=False, repr=False)

    @property
    def source_path(self) -> Path:
        return Path(self.path)

    @property
    def resolved_path(self) -> Path:
        """Path that `\\includegraphics` references. SVG → PDF in build/."""
        src = self.source_path
        if src.suffix.lower() in _PDF_COMPAT:
            return src
        if src.suffix.lower() == ".svg":
            digest = hashlib.sha1(src.resolve().as_posix().encode()).hexdigest()[:10]
            return Path("build") / f"{src.stem}-{digest}.pdf"
        raise ValueError(f"unsupported image extension: {src.suffix}")

    def ensure_converted(self) -> None:
        """Run SVG→PDF conversion if needed. Idempotent."""
        if self.source_path.suffix.lower() == ".svg":
            target = self.resolved_path
            if not target.exists():
                _convert_to_pdf(self.source_path, target)

    def read_bytes(self) -> bytes:
        """Return the bytes of the resolved (TeX-compatible) image."""
        self.ensure_converted()
        return self.resolved_path.read_bytes()

    def base64_payload(self) -> str:
        return base64.b64encode(self.read_bytes()).decode("ascii")

    @property
    @override
    def rendered(self) -> str:
        opts: list[str] = []
        if self.width is not None:
            opts.append(f"width={self.width}")
        if self.height is not None:
            opts.append(f"height={self.height}")
        if self.scale is not None:
            opts.append(f"scale={self.scale}")
        if self.keepaspectratio:
            opts.append("keepaspectratio")
        opt_str = f"[{','.join(opts)}]" if opts else ""
        return f"\\includegraphics{opt_str}{{{self.resolved_path.as_posix()}}}"

    @property
    @override
    def requires(self) -> frozenset[PackageProtocol]:
        from ..packages import GRAPHICX
        return frozenset({GRAPHICX})


def collect_inline_images(root: TeX) -> tuple[IncludeImage, ...]:
    """Walk a TeX tree, return all IncludeImage nodes with `inline_base64=True`."""
    seen: dict[str, IncludeImage] = {}

    def walk(node: TeX) -> None:
        if isinstance(node, IncludeImage) and node.inline_base64:
            key = node.resolved_path.as_posix()
            if key not in seen:
                seen[key] = node
        for child in node.children or ():
            walk(child)

    walk(root)
    return tuple(seen.values())


def filecontents_b64_block(image: IncludeImage) -> str:
    """`\\begin{filecontents*}[overwrite,nosearch]{<resolved>.b64}<base64>\\end{filecontents*}`."""
    target = image.resolved_path.as_posix() + ".b64"
    payload = image.base64_payload()
    chunks = [payload[i : i + 76] for i in range(0, len(payload), 76)]
    body = "\n".join(chunks)
    return (
        f"\\begin{{filecontents*}}[overwrite,nosearch]{{{target}}}\n"
        f"{body}\n"
        "\\end{filecontents*}"
    )


# Avoid unused-import warning
_ = attach
