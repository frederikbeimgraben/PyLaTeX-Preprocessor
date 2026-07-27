"""The HSRT report variants and the logo set that each one selects."""

from enum import Enum

__all__ = ["Variant", "default_logo_names", "footer_logo_names"]


class Variant(Enum):
    """One HSRT report variant, which selects the default title-page logos."""

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

# The footer logos default to the title-page set. A variant can replace them
# when the anchor differs. MAKERS uses the left-aligned logo at the top-left
# title anchor and the right-aligned logo at the bottom-right footer anchor.
# The icon then always faces into the page corner.
FOOTER_LOGOS: dict[Variant, tuple[str, ...]] = {
    Variant.MAKERS: ("MAKERS-RAlign",),
}


def default_logo_names(variant: Variant) -> tuple[str, ...]:
    """Return the title-page logo names of a variant.

    Returns:
        An empty tuple when the variant has no default logos.
    """
    return DEFAULT_LOGOS.get(variant, ())


def footer_logo_names(variant: Variant) -> tuple[str, ...]:
    """Return the footer logo names of a variant.

    Returns:
        The title-page logo names when the variant defines no footer set.
    """
    return FOOTER_LOGOS.get(variant, default_logo_names(variant))
