import sys

from . import packages
from .commands import (
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
from .helpers import coerce, sanitize, with_package
from .model import (
    color,
    comment,
    concat,
    control_sequence,
    document,
    document_class,
    empty,
    environment,
    image,
    include,
    length,
    math,
    package,
    raw,
)
from .registry import Registry

__all__ = [
    "Registry",
    "biblatex",
    "builtin",
    "captions",
    "cleveref",
    "coerce",
    "color",
    "colors",
    "comment",
    "concat",
    "conditionals",
    "control_sequence",
    "counters",
    "definitions",
    "document",
    "document_class",
    "empty",
    "environment",
    "floats",
    "font",
    "fontawesome",
    "fontspec",
    "geometry",
    "glossaries",
    "graphics",
    "hooks",
    "hyperref",
    "image",
    "include",
    "length",
    "lengths",
    "listings",
    "math",
    "mdframed",
    "package",
    "packages",
    "picture",
    "raw",
    "sanitize",
    "setspace",
    "tables",
    "with_package",
]

# `tex(t"...")` needs PEP 750 template strings (Python 3.14+). Exposed only
# there; the rest of the library stays importable on 3.13.
if sys.version_info >= (3, 14):
    from .template import tex as tex  # pyright: ignore[reportUnreachable]

    __all__.append("tex")
