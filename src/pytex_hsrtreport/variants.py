from enum import Enum


class Variant(Enum):
    """HSRT report variant — picks default logo set on the title page."""

    INF = "inf"
    STUPA = "stupa"
    ASTA = "asta"
    ECHO = "echo"


_DEFAULT_LOGOS: dict[Variant, tuple[str, ...]] = {
    Variant.INF: ("INF",),
    Variant.STUPA: ("STUPA",),
    Variant.ASTA: ("ASTA",),
    Variant.ECHO: ("ECHO",),
}


def default_logo_names(variant: Variant) -> tuple[str, ...]:
    return _DEFAULT_LOGOS.get(variant, ())
