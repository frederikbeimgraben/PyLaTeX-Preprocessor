from enum import Enum

__all__ = ["Variant", "default_logo_names", "footer_logo_names"]


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

# Footer logos default to the title-page set, but a variant can override them
# where the anchor differs: MAKERS uses the left-aligned logo at the top-left
# title anchor and the right-aligned one at the bottom-right footer anchor, so
# the icon always faces into the page corner.
FOOTER_LOGOS: dict[Variant, tuple[str, ...]] = {
    Variant.MAKERS: ("MAKERS-RAlign",),
}


def default_logo_names(variant: Variant) -> tuple[str, ...]:
    return DEFAULT_LOGOS.get(variant, ())


def footer_logo_names(variant: Variant) -> tuple[str, ...]:
    """Footer logo set, falling back to the title-page logos when unset."""
    return FOOTER_LOGOS.get(variant, default_logo_names(variant))
