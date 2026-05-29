"""File inclusion and raw TeX support."""

from dataclasses import dataclass
from pathlib import Path
from typing import override

from ..model.base_model import TeX


@dataclass
class IncludeTeX(TeX):
    """Include an external .tex file via \\input{path}."""

    path: str | Path

    @property
    @override
    def children(self) -> tuple["TeX", ...]:
        return tuple()

    @override
    def serialize(self, indent: int = 0) -> str:
        return self.serialize_indented(indent)

    def serialize_indented(self, _indent: int) -> str:
        path_str = str(self.path)
        if path_str.endswith(".tex"):
            path_str = path_str[:-4]
        return f"\\input{{{path_str}}}"


@dataclass
class Include(TeX):
    """Include an external .pytex file inline."""

    path: str | Path
    _cached_content: TeX | None = None

    @property
    @override
    def children(self) -> tuple["TeX", ...]:
        if self._cached_content is not None:
            return (self._cached_content,)
        return tuple()

    def load(self) -> TeX:
        path = Path(self.path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        with open(path) as f:
            code = f.read()

        namespace: dict[str, object] = {"__builtins__": __builtins__}
        exec(code, namespace)

        result: TeX | None = None
        for name in ["__pytex__", "document", "content", "root"]:
            if name in namespace:
                obj = namespace[name]
                if isinstance(obj, TeX):
                    result = obj
                    break

        if result is None:
            for value in namespace.values():
                if isinstance(value, TeX):
                    result = value
                    break

        if result is None:
            raise ValueError(
                f"No TeX object found in {path}. "
                + "Define a TeX object named '__pytex__', 'document', 'content', or 'root'."
            )

        self._cached_content = result
        return result

    @override
    def serialize(self, indent: int = 0) -> str:
        return self.serialize_indented(indent)

    def serialize_indented(self, indent: int) -> str:
        from ..model.serialization import serialize_with_indent

        if self._cached_content is None:
            self._cached_content = self.load()
        return serialize_with_indent(self._cached_content, indent)
