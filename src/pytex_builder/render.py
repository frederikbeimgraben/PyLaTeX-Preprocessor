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
from typing import TYPE_CHECKING, cast

from pytex.interface.tex import TeX
from pytex.model.include import IncludeTeX

from .tectonic import BuildError

__all__ = ["get_tex_node", "render_input"]

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

PYTEX_VAR = "__pytex__"


def _render_python(path: Path) -> TeX:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise BuildError(f"could not load Python module from {path}")

    module = importlib.util.module_from_spec(spec)
    # Let the module import siblings relative to its own directory.
    sys.path.insert(0, str(path.resolve().parent))
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        raise BuildError(f"error while importing {path.name}: {exc}") from exc
    finally:
        sys.path.pop(0)

    if not hasattr(module, PYTEX_VAR):
        raise BuildError(f"{path.name} defines no '{PYTEX_VAR}' variable to render")

    value = cast("object", getattr(module, PYTEX_VAR))
    if not isinstance(value, TeX):
        raise BuildError(
            f"'{PYTEX_VAR}' in {path.name} is {type(value).__name__};"
            + " expected a TeX node (with a '.rendered' property)"
        )
    return value


def _render_markdown(
    path: Path, variant: str | None, config: Mapping[str, object] | None
) -> TeX:
    # Imported lazily so plain .tex/.py builds need neither marko nor hsrt.
    from .variants import build_document

    return build_document(path.read_text(), variant=variant, config=config)


def get_tex_node(
    path: Path,
    *,
    variant: str | None = None,
    config: Mapping[str, object] | None = None,
) -> TeX:
    """Load ``path`` and return the TeX node without rendering.

    ``variant`` and ``config`` only affect Markdown inputs (see
    :mod:`pytex_builder.variants`); they are ignored for ``.tex``/``.py``.
    """
    suffix = path.suffix.lower()
    if suffix == ".tex":
        return IncludeTeX(path)
    if suffix == ".py":
        return _render_python(path)
    if suffix in (".md", ".markdown"):
        return _render_markdown(path, variant, config)
    raise BuildError(
        f"unsupported input type '{suffix or path.name}'; "
        + "expected .tex, .py or .md"
    )


def render_input(
    path: Path,
    *,
    variant: str | None = None,
    config: Mapping[str, object] | None = None,
) -> str:
    """Render ``path`` to a LaTeX source string."""
    return get_tex_node(path, variant=variant, config=config).rendered
