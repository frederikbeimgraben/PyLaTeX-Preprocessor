from dataclasses import dataclass, field
from typing import Final, override

from pytex.helpers.parenting import attach
from pytex.interface.package import PackageProtocol
from pytex.interface.tex import TeX
from pytex.packages import PGF, TIKZ
from pytex.registry import Registry

__all__ = [
    "Circle",
    "Coordinate",
    "Draw",
    "Fill",
    "Node",
    "Rectangle",
    "Scope",
    "TikzLibrary",
    "TikzPicture",
]

type TikzOption = str | tuple[str, str]
type TikzCoord = str | tuple[float, float] | "Coordinate" | "Node"


def _render_options(options: tuple[TikzOption, ...]) -> str:
    if not options:
        return ""
    return (
        "["
        + ",".join(o if isinstance(o, str) else f"{o[0]}={o[1]}" for o in options)
        + "]"
    )


def _render_pos(pos: TikzCoord) -> str:
    if isinstance(pos, Coordinate):
        return f"({pos.name})"
    if isinstance(pos, Node):
        if pos.name is None:
            raise ValueError("Node used as position must have a name")
        return f"({pos.name})"
    if isinstance(pos, tuple):
        return f"({pos[0]},{pos[1]})"
    if pos.startswith("("):
        return pos
    return f"({pos})"


@Registry.add
@dataclass(frozen=True)
class Coordinate(TeX):
    name: Final[str]
    at: Final[tuple[float, float] | None] = None
    options: Final[tuple[TikzOption, ...]] = ()

    @property
    @override
    def rendered(self) -> str:
        opts = _render_options(self.options)
        if self.at is None:
            return f"\\coordinate{opts} ({self.name});"
        return f"\\coordinate{opts} ({self.name}) at ({self.at[0]},{self.at[1]});"

    @property
    @override
    def requires(self) -> frozenset[PackageProtocol]:
        return frozenset({TIKZ})


@Registry.add
@dataclass(frozen=True)
class Node(TeX):
    label: Final[TeX | str] = ""
    name: Final[str | None] = None
    at: Final[TikzCoord | None] = None
    options: Final[tuple[TikzOption, ...]] = ()
    _parent: "TeX | None" = field(default=None, init=False, compare=False, repr=False)

    def __post_init__(self) -> None:
        attach(self, self.label)

    @property
    @override
    def rendered(self) -> str:
        parts: list[str] = ["\\node"]
        parts.append(_render_options(self.options))
        if self.name is not None:
            parts.append(f" ({self.name})")
        if self.at is not None:
            parts.append(f" at {_render_pos(self.at)}")
        parts.append(f" {{{self.label}}};")
        return "".join(parts)

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return (self.label,) if isinstance(self.label, TeX) else ()

    @property
    @override
    def requires(self) -> frozenset[PackageProtocol]:
        return frozenset({TIKZ})


@Registry.add
@dataclass(frozen=True)
class Draw(TeX):
    points: Final[tuple[TikzCoord, ...]]
    op: Final[str] = "--"
    options: Final[tuple[TikzOption, ...]] = ()
    cycle: Final[bool] = False

    @property
    @override
    def rendered(self) -> str:
        opts = _render_options(self.options)
        path = f" {self.op} ".join(_render_pos(p) for p in self.points)
        if self.cycle:
            path = f"{path} {self.op} cycle"
        return f"\\draw{opts} {path};"

    @property
    @override
    def requires(self) -> frozenset[PackageProtocol]:
        return frozenset({TIKZ})


@Registry.add
@dataclass(frozen=True)
class Fill(TeX):
    points: Final[tuple[TikzCoord, ...]]
    options: Final[tuple[TikzOption, ...]] = ()
    op: Final[str] = "--"

    @property
    @override
    def rendered(self) -> str:
        opts = _render_options(self.options)
        path = f" {self.op} ".join(_render_pos(p) for p in self.points)
        return f"\\fill{opts} {path} -- cycle;"

    @property
    @override
    def requires(self) -> frozenset[PackageProtocol]:
        return frozenset({TIKZ})


@Registry.add
@dataclass(frozen=True)
class Circle(TeX):
    center: Final[TikzCoord]
    radius: Final[float | str]
    options: Final[tuple[TikzOption, ...]] = ()
    fill: Final[bool] = False

    @property
    @override
    def rendered(self) -> str:
        opts = _render_options(self.options)
        cmd = "\\fill" if self.fill else "\\draw"
        return f"{cmd}{opts} {_render_pos(self.center)} circle ({self.radius});"

    @property
    @override
    def requires(self) -> frozenset[PackageProtocol]:
        return frozenset({TIKZ})


@Registry.add
@dataclass(frozen=True)
class Rectangle(TeX):
    a: Final[TikzCoord]
    b: Final[TikzCoord]
    options: Final[tuple[TikzOption, ...]] = ()
    fill: Final[bool] = False

    @property
    @override
    def rendered(self) -> str:
        opts = _render_options(self.options)
        cmd = "\\fill" if self.fill else "\\draw"
        return f"{cmd}{opts} {_render_pos(self.a)} rectangle {_render_pos(self.b)};"

    @property
    @override
    def requires(self) -> frozenset[PackageProtocol]:
        return frozenset({TIKZ})


@Registry.add
@dataclass(frozen=True)
class TikzPicture(TeX):
    elements: Final[tuple[TeX, ...]]
    options: Final[tuple[TikzOption, ...]] = ()

    def __init__(
        self,
        *elements: TeX,
        options: tuple[TikzOption, ...] = (),
    ) -> None:
        object.__setattr__(self, "elements", elements)
        object.__setattr__(self, "options", options)
        object.__setattr__(self, "_parent", None)
        attach(self, *elements)

    @property
    @override
    def rendered(self) -> str:
        opts = _render_options(self.options)
        inner = "\n".join(e.rendered for e in self.elements)
        return f"\\begin{{tikzpicture}}{opts}\n{inner}\n\\end{{tikzpicture}}"

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return self.elements

    @property
    @override
    def requires(self) -> frozenset[PackageProtocol]:
        return frozenset({TIKZ, PGF})


@Registry.add
@dataclass(frozen=True)
class TikzLibrary(TeX):
    name: Final[str]

    @property
    @override
    def rendered(self) -> str:
        return f"\\usetikzlibrary{{{self.name}}}"

    @property
    @override
    def requires(self) -> frozenset[PackageProtocol]:
        return frozenset({TIKZ})


@Registry.add
@dataclass(frozen=True)
class Scope(TeX):
    elements: Final[tuple[TeX, ...]]
    options: Final[tuple[TikzOption, ...]] = ()

    def __init__(
        self,
        *elements: TeX,
        options: tuple[TikzOption, ...] = (),
    ) -> None:
        object.__setattr__(self, "elements", elements)
        object.__setattr__(self, "options", options)
        object.__setattr__(self, "_parent", None)
        attach(self, *elements)

    @property
    @override
    def rendered(self) -> str:
        opts = _render_options(self.options)
        inner = "\n".join(e.rendered for e in self.elements)
        return f"\\begin{{scope}}{opts}\n{inner}\n\\end{{scope}}"

    @property
    @override
    def children(self) -> tuple[TeX, ...]:
        return self.elements

    @property
    @override
    def requires(self) -> frozenset[PackageProtocol]:
        return frozenset({TIKZ})
