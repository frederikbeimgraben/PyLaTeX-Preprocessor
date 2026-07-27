"""Set the parent node on the child nodes of a TeX node."""

from contextlib import suppress

from ..interface.tex import TeX

__all__ = ["attach"]


def attach(parent: TeX, *children: object) -> None:
    """Set the parent node of each TeX child to `parent`.

    The function writes `_parent` with `object.__setattr__`, because a frozen
    dataclass rejects a normal attribute assignment. The function skips a
    child that is not a TeX node. It also skips, without an error, a child
    that refuses the attribute. A node with `slots` and no `_parent` slot is
    such a child.
    """
    for child in children:
        if isinstance(child, TeX):
            with suppress(AttributeError, TypeError):
                object.__setattr__(child, "_parent", parent)
