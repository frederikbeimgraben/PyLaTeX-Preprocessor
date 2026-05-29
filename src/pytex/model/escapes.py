"""Inline Python evaluation inside raw/included LaTeX.

Two escape forms are recognised inside the text passed to :class:`~pytex.Raw`
and :class:`~pytex.IncludeTeX`:

* ``%{ pytex (EXPR) }%``
* ``\\iffalse{ pytex (EXPR) }\\fi``

``EXPR`` is a Python expression evaluated at serialization time. Its result may
be ``str`` or any :class:`~pytex.TeX` object; a ``TeX`` result is serialized,
anything else is stringified. Both forms are degenerate LaTeX no-ops, so a
document containing them still compiles even without preprocessing.

The evaluation namespace defaults to the public ``pytex`` exports plus the
standard Python builtins (so primitives and simple arithmetic work). Callers may
merge in extra objects via the ``namespace`` argument.
"""

import importlib
import re

# (opener, closer) pairs. Order matters only for readability.
_OPENERS: tuple[tuple[str, str], ...] = (
    (r"%{", "}%"),
    (r"\iffalse{", r"}\fi"),
)

# Matches the start of either construct up to and including the opening paren.
_START = re.compile(r"(%\{|\\iffalse\{)\s*pytex\s*\(")

_default_ns_cache: dict[str, object] | None = None


def default_namespace() -> dict[str, object]:
    """Public ``pytex`` exports usable inside an escape expression."""
    global _default_ns_cache
    if _default_ns_cache is None:
        # Dynamic import avoids a static import cycle (pytex -> ... -> escapes).
        module = importlib.import_module("pytex")
        names: list[str] = list(getattr(module, "__all__", []))
        _default_ns_cache = {name: getattr(module, name) for name in names}
    return dict(_default_ns_cache)


def _closer_for(opener: str) -> str:
    for start, end in _OPENERS:
        if start == opener:
            return end
    raise KeyError(opener)


def _match_balanced_paren(text: str, start: int) -> int:
    """Return index just past the ``)`` matching the ``(`` at ``start - 1``.

    ``start`` points at the first character of the expression (right after the
    opening paren). String literals are tracked so parens inside them do not
    affect the balance.
    """
    depth = 1
    i = start
    n = len(text)
    quote: str | None = None
    while i < n:
        ch = text[i]
        if quote is not None:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = None
        elif ch in "'\"":
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise ValueError("Unbalanced parentheses in pytex escape expression")


def _render_value(value: object) -> str:
    from .base_model import TeX

    if isinstance(value, TeX):
        return value.serialize()
    return str(value)


def evaluate_escapes(
    text: str,
    namespace: dict[str, object] | None = None,
    escape_spaces: bool = False,
) -> str:
    """Evaluate every ``pytex`` escape in ``text`` and return the result.

    Literal (non-escape) segments are space-escaped (``" " -> "~"``) only when
    ``escape_spaces`` is true; evaluated results are always inserted verbatim.
    When ``text`` contains no escapes the function reduces to the previous
    ``Raw`` behaviour (optionally space-escaping the whole string).
    """

    def escape(segment: str) -> str:
        return segment.replace(" ", "~") if escape_spaces else segment

    ns = default_namespace()
    if namespace:
        ns.update(namespace)

    out: list[str] = []
    pos = 0
    for m in _START.finditer(text):
        if m.start() < pos:
            # Inside a region already consumed by a previous (longer) match.
            continue
        opener = m.group(1)
        expr_start = m.end()
        try:
            expr_end = _match_balanced_paren(text, expr_start)
        except ValueError:
            continue
        closer = _closer_for(opener)
        rest = text[expr_end:]
        stripped = rest.lstrip()
        ws_len = len(rest) - len(stripped)
        if not stripped.startswith(closer):
            # Not a well-formed escape; leave it untouched.
            continue

        out.append(escape(text[pos : m.start()]))
        expr = text[expr_start : expr_end - 1]
        value: object = eval(expr, {"__builtins__": __builtins__}, ns)  # noqa: S307  # pyright: ignore[reportAny]
        out.append(_render_value(value))
        pos = expr_end + ws_len + len(closer)

    out.append(escape(text[pos:]))
    return "".join(out)
