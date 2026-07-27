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

__all__ = ["IncludeImage", "collect_inline_images", "filecontents_b64_block"]

PDF_COMPAT = {".pdf", ".png", ".jpg", ".jpeg", ".eps"}


def _convert_to_pdf(src: Path, dst: Path) -> None:
    """Convert an SVG file to a PDF file with inkscape.

    Raises:
        ValueError: `src` does not end with `.svg`.
        FileNotFoundError: The system has no inkscape binary.
        subprocess.CalledProcessError: inkscape exits with an error.
    """
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
    """An `\\includegraphics` line, with an option to inline the image.

    `IncludeImage` accepts the formats that LaTeX reads, and it also accepts
    `.svg`. It converts an SVG source to PDF with inkscape. The conversion is
    lazy. It runs only when a caller reads the image bytes.

    When `inline_base64` is True, `Document` collects this node and renders a
    `\\begin{filecontents*}[overwrite,nosearch]{<resolved>.b64}` block at the
    start of the document. The block holds the base64 text of the image. A
    build helper can decode the block to disk before the compile pass. The
    `\\includegraphics` line does not change.

    Attributes:
        width: A LaTeX length for the `width` key, for example `0.5\\textwidth`.
            None leaves the key out.
        height: A LaTeX length for the `height` key. None leaves the key out.
        scale: A scale factor as a string, for example `0.5`. None leaves the
            key out.
        keepaspectratio: True adds the `keepaspectratio` key.
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
        """The path that `\\includegraphics` references.

        A source that LaTeX reads directly keeps its own path. An SVG source
        maps to a converted PDF under the literal `build` directory.

        Raises:
            ValueError: The file extension is neither `.svg` nor one that
                LaTeX reads.
        """
        src = self.source_path
        if src.suffix.lower() in PDF_COMPAT:
            return src
        if src.suffix.lower() == ".svg":
            # The cache key is a hash of the SVG bytes, not of the path. An
            # edited source therefore gets a new name and inkscape converts it
            # again. A path-derived name would reuse a stale PDF.
            digest = hashlib.sha1(src.read_bytes()).hexdigest()[:10]
            return Path("build") / f"{src.stem}-{digest}.pdf"
        raise ValueError(f"unsupported image extension: {src.suffix}")

    def ensure_converted(self) -> None:
        """Convert the SVG source to PDF when that PDF does not exist yet.

        The method does nothing for a source that is not an SVG file. You can
        call it more than once.
        """
        if self.source_path.suffix.lower() == ".svg":
            target = self.resolved_path
            if not target.exists():
                _convert_to_pdf(self.source_path, target)

    def read_bytes(self) -> bytes:
        """Read the bytes of the resolved image, and convert an SVG source first."""
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
    """Find every `IncludeImage` node in a node tree that sets `inline_base64`.

    Returns:
        One node for each distinct resolved path, in the order the walk first
        meets it.
    """
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
    """Render a `filecontents*` block that holds the image as base64 text.

    The block writes to the resolved image path plus the `.b64` suffix. The
    base64 text wraps at 76 characters per line.
    """
    target = image.resolved_path.as_posix() + ".b64"
    payload = image.base64_payload()
    chunks = [payload[i : i + 76] for i in range(0, len(payload), 76)]
    body = "\n".join(chunks)
    # The trailing newline is required. LaTeX ignores the rest of the line
    # after \end{filecontents*}, so without the newline it drops the next
    # token. That token is another block or the start of the preamble.
    return (
        f"\\begin{{filecontents*}}[overwrite,nosearch]{{{target}}}\n"
        f"{body}\n"
        "\\end{filecontents*}\n"
    )


# No node in this module calls `attach`. This binding stops the linter from
# reporting the import as unused.
_ = attach
