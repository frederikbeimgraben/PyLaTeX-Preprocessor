from os import PathLike
from pathlib import Path

from ..registry import Registry
from .raw import Raw


@Registry.add
def IncludeTeX(
    path: str | PathLike[str],
    namespace: dict[str, object] | None = None,
    allow_replacements: bool = True,
) -> Raw:
    content = Path(path).read_text()
    return Raw(
        content,
        namespace=namespace,
        allow_replacements=allow_replacements,
    )
