from ..interface.tex import TeX


def attach(parent: TeX, *children: object) -> None:
    """Set `_parent` on each TeX child to `parent`. Non-TeX children are skipped."""
    for child in children:
        if isinstance(child, TeX):
            try:
                object.__setattr__(child, "_parent", parent)
            except (AttributeError, TypeError):
                pass
