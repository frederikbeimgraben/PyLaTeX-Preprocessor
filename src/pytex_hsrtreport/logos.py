from dataclasses import dataclass, field
from typing import Final, override

from pytex.commands.graphics import Includegraphics
from pytex.helpers.parenting import attach
from pytex.interface.tex import TeX
from pytex.model.concat import Concat
from pytex.model.raw import Raw
from pytex.registry import Registry


@Registry.add
@dataclass(frozen=True)
class Logo(TeX):
    """Single logo declaration: path + scale. Renders as `\\includegraphics`."""

    path: Final[str]
    scale: Final[float] = 1.0

    @property
    @override
    def rendered(self) -> str:
        return Includegraphics(self.path, scale=str(self.scale)).rendered


@Registry.add
@dataclass
class LogoSet(TeX):
    """Ordered set of logos. Renders all sequentially with horizontal padding."""

    logos: Final[tuple[Logo, ...]] = ()
    separator: Final[str] = "\\hspace{0.5cm}"
    _parent: "TeX | None" = field(
        default=None, init=False, compare=False, repr=False
    )

    def __post_init__(self) -> None:
        attach(self, *self.logos)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return tuple(self.logos)

    @property
    @override
    def rendered(self) -> str:
        if not self.logos:
            return ""
        return Concat(
            *(
                lg
                if i == 0
                else Concat(Raw(self.separator), lg)
                for i, lg in enumerate(self.logos)
            )
        ).rendered


def logo_set_from_paths(
    base_path: str,
    entries: tuple[tuple[str, float], ...],
    extension: str = ".pdf",
) -> LogoSet:
    """Build a LogoSet by resolving each name against `base_path`."""
    sep = "/" if not base_path.endswith("/") else ""
    return LogoSet(
        tuple(Logo(f"{base_path}{sep}{name}{extension}", scale) for name, scale in entries)
    )
