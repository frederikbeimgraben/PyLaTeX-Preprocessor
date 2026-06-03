from enum import Enum

__all__ = ["Variant", "default_logo_names"]


class Variant(Enum):
    """HSRT report variant — picks default logo set on the title page."""

    INF = "inf"
    STUPA = "stupa"
    ASTA = "asta"
    ECHO = "echo"
    MAKERS = "makers"


DEFAULT_LOGOS: dict[Variant, tuple[str, ...]] = {
    Variant.INF: ("INF",),
    Variant.STUPA: ("STUPA",),
    Variant.ASTA: ("ASTA",),
    Variant.ECHO: ("ECHO",),
    Variant.MAKERS: ("MAKERS",),
}


def default_logo_names(variant: Variant) -> tuple[str, ...]:
    return DEFAULT_LOGOS.get(variant, ())
