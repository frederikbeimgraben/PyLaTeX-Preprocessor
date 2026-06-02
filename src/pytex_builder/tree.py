"""Render a `TeX` node tree in the style of the `tree` command.

    Document
    ├── ControlSequence \\title
    │   └── Parameter {} Raw "PyTeX Example"
    └── Concat
        ├── ControlSequence \\maketitle
        └── ...

Walks the canonical `TeX.children`, so every node that exposes its structural
children shows up. `Package` instances are skipped — they are document
dependencies, not part of the syntax tree.
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
    """Collapse `WithPackage` wrappers, returning the wrapped node and the
    packages it attaches (so they can be shown connected to that node)."""
    packages: list[str] = []
    current: TeX = node
    while isinstance(current, WithPackage):
        packages.append(_package_name(current.package))
        current = cast("TeX", current.child)
    return current, packages


def _cs_arg_text(cs: ControlSequence[Parameters]) -> str | None:
    """Text of a control sequence's first argument (e.g. the env name in
    ``\\begin{name}``)."""
    for param in cs.params or ():
        value = getattr(param, "value", None)
        if isinstance(value, Raw):
            return value.content
        if isinstance(value, str):
            return value
    return None


def _as_environment(node: TeX) -> tuple[str, list[TeX]] | None:
    """If `node` is the `Concat(\\begin{X}, body..., \\end{X})` shape produced by
    `Environment`, return ``(X, body_children)``; otherwise `None`."""
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


def _children(node: TeX) -> list[TeX]:
    real, _ = _unwrap(node)
    environment = _as_environment(real)
    members = environment[1] if environment is not None else (real.children or ())
    return [child for child in members if not isinstance(child, PackageProtocol)]


def _short(text: str, limit: int = 50) -> str:
    # Show whitespace literally so a single space (e.g. the separator in
    # `\item x`) is distinguishable from an empty string. Newlines/tabs become
    # visible escapes rather than being collapsed away.
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
        return f'{head} {_paint(chr(34) + content + chr(34), color, _Paint.GREEN)}'

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
    if environment is not None:
        head = _paint("Environment", color, _Paint.BOLD)
        label = f"{head} {_paint('{' + environment[0] + '}', color, _Paint.CYAN)}"
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
    """Return the node tree as a multi-line, `tree`-style string."""
    lines = [_label(node, color)]
    _walk(node, "", color, lines)
    return "\n".join(lines)
