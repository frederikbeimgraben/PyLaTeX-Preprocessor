"""Turn an input file into a rendered LaTeX string.

Two input kinds are supported:

* ``.tex`` - wrapped in :func:`pytex.model.include.IncludeTeX` so ``\\iffalse``
  ``pytex(...)`` replacements are evaluated, then rendered.
* ``.py``  - imported as a module; its module-level ``__pytex__`` value is
  rendered. It must implement the :class:`pytex.interface.tex.TeX` protocol.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import cast

from pytex.interface.tex import TeX
from pytex.model.include import IncludeTeX

from .tectonic import BuildError

_PYTEX_VAR = "__pytex__"


def _render_python(path: Path) -> TeX:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise BuildError(f"could not load Python module from {path}")

    module = importlib.util.module_from_spec(spec)
    # Let the module import siblings relative to its own directory.
    sys.path.insert(0, str(path.resolve().parent))
    try:
        spec.loader.exec_module(module)
    except Exception as exc:  # noqa: BLE001 - surface any import-time failure
        raise BuildError(f"error while importing {path.name}: {exc}") from exc
    finally:
        sys.path.pop(0)

    if not hasattr(module, _PYTEX_VAR):
        raise BuildError(f"{path.name} defines no '{_PYTEX_VAR}' variable to render")

    value = cast(object, getattr(module, _PYTEX_VAR))
    if not isinstance(value, TeX):
        raise BuildError(
            f"'{_PYTEX_VAR}' in {path.name} is {type(value).__name__};"
            + " expected a TeX node (with a '.rendered' property)"
        )
    return value


def _render_markdown(path: Path) -> TeX:
    # Imported lazily so plain .tex/.py builds need neither marko nor hsrt.
    from pytex.model.document import Document
    from pytex_markdown import IncludeMarkdown

    return Document(IncludeMarkdown(path))


def render_input(path: Path) -> str:
    """Render ``path`` to a LaTeX source string."""
    suffix = path.suffix.lower()
    if suffix == ".tex":
        return IncludeTeX(path).rendered
    if suffix == ".py":
        return _render_python(path).rendered
    if suffix in (".md", ".markdown"):
        return _render_markdown(path).rendered
    raise BuildError(
        f"unsupported input type '{suffix or path.name}'; "
        + "expected .tex, .py or .md"
    )
