# pyright: reportUnsupportedDunderAll=false
"""Model subpackage.

Modules are not eager-imported here to avoid a circular import:
`pytex/__init__.py` → `pytex.packages` → `pytex.model.package` →
`pytex.model.__init__` → `pytex.model.math` → `pytex.packages` (still loading).

Import submodules directly: `from pytex.model.math import Frac`.
"""

__all__ = [
    "color",
    "concat",
    "control_sequence",
    "document",
    "document_class",
    "empty",
    "environment",
    "image",
    "include",
    "length",
    "math",
    "package",
    "raw",
]
