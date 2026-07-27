"""Factories that render LaTeX control sequences and environments.

Each submodule holds the factories for one LaTeX package, or for one group of
kernel commands. This package imports every submodule, so `Registry` then
holds the registry key of every factory.
"""

from . import (
    biblatex,
    builtin,
    captions,
    cleveref,
    colors,
    conditionals,
    counters,
    definitions,
    floats,
    font,
    fontawesome,
    fontspec,
    geometry,
    glossaries,
    graphics,
    hooks,
    hyperref,
    lengths,
    listings,
    mdframed,
    picture,
    setspace,
    tables,
)

__all__ = [
    "biblatex",
    "builtin",
    "captions",
    "cleveref",
    "colors",
    "conditionals",
    "counters",
    "definitions",
    "floats",
    "font",
    "fontawesome",
    "fontspec",
    "geometry",
    "glossaries",
    "graphics",
    "hooks",
    "hyperref",
    "lengths",
    "listings",
    "mdframed",
    "picture",
    "setspace",
    "tables",
]
