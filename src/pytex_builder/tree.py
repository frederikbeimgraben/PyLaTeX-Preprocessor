"""Render a node tree in the style of the `tree` command.

    Document
    ├── ControlSequence \\title
    │   └── Parameter {} Raw "PyTeX Example"
    └── Concat
        ├── ControlSequence \\maketitle
        └── ...

This module walks the canonical `TeX.children`, so every node that exposes its
child nodes appears. The module skips a `Package` instance. A package is a
package requirement of the document, not a part of the node tree.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, cast

from pytex.helpers.with_package import WithPackage
from pytex.interface.package import PackageProtocol
from pytex.model.concat import Concat
from pytex.model.control_sequence import ControlSequence
from pytex.model.raw import Raw

if TYPE_CHECKING:
    from pytex.interface.control_sequence import Parameters
    from pytex.interface.tex import TeX

__all__ = ["render_tree"]


class _Paint:
    RESET: Final = "\033[0m"
    DIM: Final = "\033[2m"
    BOLD: Final = "\033[1m"
    CYAN: Final = "\033[36m"
    GREEN: Final = "\033[32m"
    YELLOW: Final = "\033[33m"


def _paint(text: str, color: bool, *codes: str) -> str:
    return f"{''.join(codes)}{text}{_Paint.RESET}" if color and codes else text


def _package_name(pkg: object) -> str:
    return pkg.name if isinstance(pkg, PackageProtocol) else str(pkg)


def _unwrap(node: TeX) -> tuple[TeX, list[str]]:
    """Collapse the `WithPackage` wrappers around a node.

    Returns:
        The wrapped node and the names of the packages that the wrappers
        attach. The caller shows those names next to that node.
    """
    packages: list[str] = []
    current: TeX = node
    while isinstance(current, WithPackage):
        packages.append(_package_name(current.package))
        current = cast("TeX", current.child)
    return current, packages


def _cs_arg_text(cs: ControlSequence[Parameters]) -> str | None:
    """Return the text of the first argument of a control sequence.

    One example is the environment name in `\\begin{name}`.

    Returns:
        The argument text, or `None` when no argument holds text.
    """
    for param in cs.params or ():
        value = getattr(param, "value", None)
        if isinstance(value, Raw):
            return value.content
        if isinstance(value, str):
            return value
    return None


def _as_environment(node: TeX) -> tuple[str, list[TeX]] | None:
    """Recognize the `Concat(\\begin{X}, body..., \\end{X})` shape of `Environment`.

    Returns:
        The environment name and its body child nodes. The result is `None`
        when `node` does not have that shape.
    """
    if not isinstance(node, Concat):
        return None
    kids = list(node.children or ())
    if len(kids) < 2:
        return None
    first, last = kids[0], kids[-1]
    if not (
        isinstance(first, ControlSequence)
        and first.name == "begin"
        and isinstance(last, ControlSequence)
        and last.name == "end"
    ):
        return None
    name = _cs_arg_text(cast("ControlSequence[Parameters]", first))
    if name is None or name != _cs_arg_text(cast("ControlSequence[Parameters]", last)):
        return None
    return name, kids[1:-1]


def _as_math(node: TeX) -> tuple[str, list[TeX]] | None:
    """Recognize a math `Concat` node and return its label and its body.

    `Math` produces `\\(..\\)`, `DisplayMath` produces `\\[..\\]`, and
    `InlineMath` produces `$..$`.

    Returns:
        The label, which is `Math`, `DisplayMath` or `InlineMath`, and the body
        child nodes. The result is `None` when `node` is not a math node.
    """
    if not isinstance(node, Concat):
        return None
    kids = list(node.children or ())
    if len(kids) < 2:
        return None
    first, last = kids[0], kids[-1]
    if isinstance(first, ControlSequence) and isinstance(last, ControlSequence):
        if first.name == "[" and last.name == "]":
            return "DisplayMath", kids[1:-1]
        if first.name == "(" and last.name == ")":
            return "Math", kids[1:-1]
    if (
        isinstance(first, Raw)
        and first.content == "$"
        and isinstance(last, Raw)
        and last.content == "$"
    ):
        return "InlineMath", kids[1:-1]
    return None


def _children(node: TeX) -> list[TeX]:
    real, _ = _unwrap(node)
    group = _as_environment(real) or _as_math(real)
    members = group[1] if group is not None else (real.children or ())
    return [child for child in members if not isinstance(child, PackageProtocol)]


def _short(text: str, limit: int = 50) -> str:
    # Show a newline and a tab as a visible escape. Keep a single space visible
    # too, so the reader can tell the separator in `\item x` from an empty
    # string.
    shown = text.replace("\n", "\\n").replace("\t", "\\t")
    if len(shown) > limit:
        shown = shown[: limit - 1] + "…"
    return shown


def _base_label(node: TeX, color: bool) -> str:
    cls = type(node).__name__
    head = _paint(cls, color, _Paint.BOLD)

    name = getattr(node, "name", None)
    if isinstance(name, str) and cls != "Package":
        return f"{head} {_paint(chr(92) + name, color, _Paint.CYAN)}"

    if cls == "Raw":
        content = _short(str(getattr(node, "content", "")))
        return f"{head} {_paint(chr(34) + content + chr(34), color, _Paint.GREEN)}"

    if cls == "Comment":
        content = _short(str(getattr(node, "text", "")))
        return f"{head} {_paint(chr(37) + content, color, _Paint.DIM)}"

    if cls == "Parameter":
        braces = "[ ]" if getattr(node, "optional", False) else "{ }"
        return f"{head} {_paint(braces, color, _Paint.DIM)}"

    if cls == "Document":
        cls_name = str(getattr(node, "document_class", ""))
        return f"{head} {_paint('(' + cls_name + ')', color, _Paint.DIM)}"

    return head


def _label(node: TeX, color: bool) -> str:
    real, packages = _unwrap(node)
    environment = _as_environment(real)
    math = _as_math(real)
    if environment is not None:
        head = _paint("Environment", color, _Paint.BOLD)
        label = f"{head} {_paint('{' + environment[0] + '}', color, _Paint.CYAN)}"
    elif math is not None:
        label = _paint(math[0], color, _Paint.BOLD)
    else:
        label = _base_label(real, color)
    if packages:
        tag = "+" + ", ".join(dict.fromkeys(packages))
        label += " " + _paint(f"[{tag}]", color, _Paint.YELLOW)
    return label


def _walk(node: TeX, prefix: str, color: bool, lines: list[str]) -> None:
    children = _children(node)
    for index, child in enumerate(children):
        last = index == len(children) - 1
        branch = "└── " if last else "├── "
        extension = "    " if last else "│   "
        if color:
            branch = f"{_Paint.DIM}{branch}{_Paint.RESET}"
            extension = f"{_Paint.DIM}{extension}{_Paint.RESET}"
        lines.append(f"{prefix}{branch}{_label(child, color)}")
        _walk(child, prefix + extension, color, lines)


def render_tree(node: TeX, color: bool = False) -> str:
    """Return the node tree as a multi-line string in the style of `tree`."""
    lines = [_label(node, color)]
    _walk(node, "", color, lines)
    return "\n".join(lines)
