from enum import Enum


class Variant(Enum):
    METI = "meti"
    MKI = "mki"
    HUC = "huc"
    STUPA = "stupa"
    ASTA = "asta"
    ECHO = "echo"


_DEFAULT_LOGOS: dict[Variant, tuple[tuple[str, float], ...]] = {
    Variant.METI: (("INF", 1.0), ("METI", 1.0)),
    Variant.MKI: (("INF", 1.0), ("MKI", 1.0)),
    Variant.HUC: (("INF", 1.0), ("HUC", 1.0)),
    Variant.STUPA: (("STUPA", 1.0),),
    Variant.ASTA: (("ASTA", 1.0),),
    Variant.ECHO: (("ECHO", 1.0),),
}


def default_logos(variant: Variant) -> tuple[tuple[str, float], ...]:
    return _DEFAULT_LOGOS.get(variant, ())
