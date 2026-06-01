from contextlib import suppress

from ..interface.tex import TeX

__all__ = ["attach"]


def attach(parent: TeX, *children: object) -> None:
    """Set `_parent` on each TeX child to `parent`. Non-TeX children are skipped."""
    for child in children:
        if isinstance(child, TeX):
            with suppress(AttributeError, TypeError):
                object.__setattr__(child, "_parent", parent)
