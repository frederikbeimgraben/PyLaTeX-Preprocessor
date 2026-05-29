"""LaTeX graphics inclusion: \\includegraphics."""

from dataclasses import dataclass
from typing import override

from ...model.base_model import Package, TeX


@dataclass
class IncludeGraphics(TeX):
    """\\includegraphics[options]{path} — requires graphicx package."""

    path: str
    width: str | None = None
    height: str | None = None
    scale: float | None = None
    angle: float | None = None

    @property
    @override
    def required_packages(self) -> set[Package | str]:
        return {"graphicx"}

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return ()

    @override
    def serialize(self) -> str:
        opts: list[str] = []
        if self.width is not None:
            opts.append(f"width={self.width}")
        if self.height is not None:
            opts.append(f"height={self.height}")
        if self.scale is not None:
            opts.append(f"scale={self.scale}")
        if self.angle is not None:
            opts.append(f"angle={self.angle}")
        opt_str = f"[{','.join(opts)}]" if opts else ""
        return f"\\includegraphics{opt_str}{{{self.path}}}"
