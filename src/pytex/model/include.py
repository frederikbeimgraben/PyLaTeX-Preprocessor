from os import PathLike
from pathlib import Path

from ..registry import Registry
from .raw import Raw

__all__ = ["IncludeTeX"]


@Registry.add
def IncludeTeX(
    path: str | PathLike[str],
    namespace: dict[str, object] | None = None,
    allow_replacements: bool = True,
) -> Raw:
    """Read a `.tex` file and return its content as a `Raw` node.

    Args:
        namespace: Extra names for the inline `pytex(...)` markers. None means
            no extra names.
        allow_replacements: True runs each inline `pytex(...)` marker in the
            file as Python code. This is code execution by design. Pass False
            for a file from a source you do not trust.
    """
    content = Path(path).read_text()
    return Raw(
        content,
        namespace=namespace,
        allow_replacements=allow_replacements,
    )
