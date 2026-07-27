"""Turn an input file into a rendered LaTeX string.

PyTeX supports three input kinds:

* A `.tex` file. PyTeX wraps it in `IncludeTeX`, evaluates the inline
  `pytex(...)` markers, and renders the result.
* A `.tex.py` file. PyTeX imports it as a module and renders the module-level
  `__pytex__` node. That node must implement the `TeX` protocol.
* A Markdown file. PyTeX passes it to the Markdown converter, which wraps the
  result in the document for the chosen variant.
"""

from __future__ import annotations

import importlib.util
import re
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

# A t-string literal prefix (PEP 750): an optional `r` before or after the `t`,
# then a quote. PyTeX uses this pattern only to add a hint when such a file
# fails to parse on Python 3.13 or earlier.
_TSTRING_PREFIX = re.compile(r"""(?<![A-Za-z0-9_])[rR]?[tT][rR]?['"]""")


def _import_error_message(path: Path, exc: SyntaxError) -> str:
    """Build the error message for a `.tex.py` file that fails to parse.

    A PyTeX document can use the t-string syntax (`t"..."`) of Python 3.14. An
    import on an older interpreter then fails with a bare `SyntaxError`. Such a
    message does not name the cause, so this function adds a hint.

    Returns:
        The message text. It ends with the t-string hint only when the running
        Python is older than 3.14 and the source matches `_TSTRING_PREFIX`.
    """
    base = f"error while importing {path.name}: {exc}"
    # Read the running version through indexing, not through the
    # `sys.version_info` tuple itself. A comparison on the tuple lets the type
    # checker prune one branch as unreachable. The pruned branch then depends
    # on the interpreter that runs the checker.
    major, minor = sys.version_info[0], sys.version_info[1]
    if (major, minor) >= (3, 14):
        return base
    try:
        source = path.read_text(encoding="utf-8")
    except OSError:
        return base
    if _TSTRING_PREFIX.search(source) is None:
        return base
    return (
        base
        + '\nthis file appears to use t-string syntax (t"..."), which needs '
        + f"Python 3.14; you are on Python {major}.{minor}"
    )


def _render_python(path: Path) -> TeX:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise BuildError(f"could not load Python module from {path}")

    module = importlib.util.module_from_spec(spec)
    # The module can import a sibling module by name, so PyTeX puts the
    # directory of the module first on `sys.path`.
    sys.path.insert(0, str(path.resolve().parent))
    try:
        spec.loader.exec_module(module)
    except SyntaxError as exc:
        raise BuildError(_import_error_message(path, exc)) from exc
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
    # Import late, so that a `.tex` or `.tex.py` build needs neither marko nor
    # `pytex_hsrtreport`.
    from .variants import build_document

    return build_document(path.read_text(), variant=variant, config=config)


def get_tex_node(
    path: Path,
    *,
    variant: str | None = None,
    config: Mapping[str, object] | None = None,
) -> TeX:
    """Load `path` and return the TeX node, without rendering it.

    Args:
        variant: The variant for a Markdown input file. See
            `pytex_builder.variants`. `None` lets PyTeX detect the variant. A
            `.tex` or `.tex.py` input file ignores this value.
        config: Document-class parameters that override the frontmatter of a
            Markdown input file. A `.tex` or `.tex.py` input file ignores this
            value.

    Raises:
        BuildError: PyTeX does not support the suffix of `path`.
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
    """Render `path` and return the LaTeX source string."""
    return get_tex_node(path, variant=variant, config=config).rendered
