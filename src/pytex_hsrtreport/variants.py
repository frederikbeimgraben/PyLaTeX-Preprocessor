"""Report variants and their default logo sets.

A *variant* selects the faculty/organisation a report belongs to and drives the
default logos placed on the title page and footer. The caller may override the
defaults via the ``logos`` argument of :func:`pytex_hsrtreport.HSRTReport`.
"""

from typing import Literal

#: Supported report variants.
type Variant = Literal[
    "INF_meti",
    "INF_mki",
    "INF_huc",
    "STUPA",
    "ASTA",
    "ECHO",
]

#: Logo names known to ship as PDFs under ``Assets/Images/Logos``.
type Logo = Literal[
    "INF/Kombiniert",
    "INF/Simple",
    "HSRT",
    "STUPA/Black",
    "STUPA/Gray",
    "STUPA/Mono/Black",
]

#: Default ordered logo set per variant.
VARIANT_LOGOS: dict[str, tuple[str, ...]] = {
    "INF_meti": ("INF/Kombiniert", "HSRT"),
    "INF_mki": ("INF/Kombiniert", "HSRT"),
    "INF_huc": ("INF/Kombiniert", "HSRT"),
    "STUPA": ("STUPA/Black", "HSRT"),
    "ASTA": ("HSRT",),
    "ECHO": ("HSRT",),
}

#: Default scale applied to a logo when no explicit scale is given.
DEFAULT_LOGO_SCALE = 0.9


def resolve_logos(
    variant: str,
    logos: set[str] | list[str] | tuple[str, ...] | dict[str, float] | None = None,
) -> list[tuple[str, float]]:
    """Return the ordered ``(name, scale)`` logo list for a document.

    ``logos`` overrides the variant default. It may be a set/sequence of logo
    names (scaled with :data:`DEFAULT_LOGO_SCALE`) or a ``{name: scale}`` map.
    """
    if logos is None:
        names = VARIANT_LOGOS.get(variant, ("HSRT",))
        return [(name, DEFAULT_LOGO_SCALE) for name in names]

    if isinstance(logos, dict):
        return [(name, scale) for name, scale in logos.items()]

    return [(name, DEFAULT_LOGO_SCALE) for name in logos]
