from dataclasses import dataclass
from typing import override

from ..interface.package import PackageProtocol
from ..interface.tex import TeX
from ..registry import Registry

__all__ = [
    "Color",
    "ColorSpec",
    "collect_colors",
    "is_known_color_name",
    "register_named_color",
]

NAMED_COLORS: set[str] = {
    "black",
    "white",
    "red",
    "green",
    "blue",
    "cyan",
    "magenta",
    "yellow",
    "gray",
    "lightgray",
    "darkgray",
    "orange",
    "violet",
    "purple",
    "brown",
    "pink",
    "olive",
    "lime",
    "teal",
}


def register_named_color(name: str) -> None:
    """Whitelist a name so `Color.named(name)` accepts it."""
    NAMED_COLORS.add(name)


def is_known_color_name(name: str) -> bool:
    return name in NAMED_COLORS


@dataclass(frozen=True)
class ColorSpec:
    """Frozen colour identity: `model` + `value` for `\\definecolor`."""

    model: str
    value: str


@Registry.add
class Color(TeX):
    """Type-safe colour reference.

    Constructors:
        Color("blue")                 # registered name
        Color("#FF0000")              # hex
        Color((255, 0, 0))            # rgb 0..255
        Color((1.0, 0.0, 0.0))        # rgb 0..1
        Color.hex("FF0000")
        Color.rgb255(255, 0, 0)
        Color.rgb(1.0, 0.0, 0.0)
        Color.named("blue")
    """

    name: str
    spec: ColorSpec | None
    _parent: "TeX | None"

    def __init__(
        self,
        value: "str | tuple[int, int, int] | tuple[float, float, float] | None" = None,
        *,
        name: str | None = None,
        spec: ColorSpec | None = None,
    ) -> None:
        if value is not None:
            resolved_name, resolved_spec = _from_overload(value)
            self.name = resolved_name
            self.spec = resolved_spec
        elif name is not None:
            self.name = name
            self.spec = spec
        else:
            raise TypeError("Color() requires `value` or `name`")
        self._parent = None

    @classmethod
    def hex(cls, value: str, name: str | None = None) -> "Color":
        clean = value.lstrip("#").upper()
        if len(clean) != 6 or any(c not in "0123456789ABCDEF" for c in clean):
            raise ValueError(f"invalid hex colour: {value!r}")
        return cls(name=name or f"c{clean}", spec=ColorSpec("HTML", clean))

    @classmethod
    def rgb255(cls, r: int, g: int, b: int, name: str | None = None) -> "Color":
        for v in (r, g, b):
            if not 0 <= v <= 255:
                raise ValueError(f"rgb255 component out of range: {v}")
        return cls(
            name=name or f"c{r:03d}{g:03d}{b:03d}",
            spec=ColorSpec("RGB", f"{r},{g},{b}"),
        )

    @classmethod
    def rgb(cls, r: float, g: float, b: float, name: str | None = None) -> "Color":
        for v in (r, g, b):
            if not 0.0 <= float(v) <= 1.0:
                raise ValueError(f"rgb component out of range [0,1]: {v}")
        return cls(
            name=name or f"crgb{int(r * 255):03d}{int(g * 255):03d}{int(b * 255):03d}",
            spec=ColorSpec("rgb", f"{r},{g},{b}"),
        )

    @classmethod
    def named(cls, name: str) -> "Color":
        if not is_known_color_name(name):
            raise ValueError(
                f"unknown colour name {name!r}; register via register_named_color"
            )
        return cls(name=name, spec=None)

    def tint(self, percent: int) -> "Color":
        """xcolor tint: `<self>!<percent>` (e.g. `blue!20`)."""
        return Color(name=f"{self.name}!{percent}", spec=None)

    def mix(self, other: "Color", percent: int = 50) -> "Color":
        return Color(
            name=f"{self.name}!{percent}!{other.name}",
            spec=None,
        )

    def __or__(self, other: "Color") -> "Color":
        return self.mix(other)

    @override
    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Color)
            and self.name == other.name
            and self.spec == other.spec
        )

    @override
    def __hash__(self) -> int:
        return hash((self.name, self.spec))

    @override
    def __repr__(self) -> str:
        return f"Color(name={self.name!r}, spec={self.spec!r})"

    @property
    @override
    def rendered(self) -> str:
        return self.name

    @property
    @override
    def requires(self) -> frozenset[PackageProtocol]:
        from ..packages import XCOLOR

        return frozenset({XCOLOR})


def _from_overload(
    value: "str | tuple[int, int, int] | tuple[float, float, float]",
) -> tuple[str, ColorSpec | None]:
    if isinstance(value, str):
        if value.startswith("#"):
            c = Color.hex(value)
            return c.name, c.spec
        if not is_known_color_name(value):
            raise ValueError(f"unknown colour name {value!r}")
        return value, None
    if len(value) == 3:
        if all(type(v) is int for v in value):
            r, g, b = value
            c = Color.rgb255(int(r), int(g), int(b))
            return c.name, c.spec
        if all(isinstance(v, float) for v in value):
            r, g, b = value
            c = Color.rgb(float(r), float(g), float(b))
            return c.name, c.spec
    raise TypeError(f"cannot construct Color from {value!r}")


def collect_colors(root: TeX) -> tuple[Color, ...]:
    """Walk a TeX tree, return all unique `Color` instances with a `spec`."""
    seen: dict[str, Color] = {}

    def walk(node: TeX) -> None:
        if isinstance(node, Color) and node.spec is not None and node.name not in seen:
            seen[node.name] = node
        for child in node.children or ():
            walk(child)

    walk(root)
    return tuple(seen.values())
