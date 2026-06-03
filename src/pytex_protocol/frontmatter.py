"""Minimal YAML-frontmatter splitter for protocol Markdown files.

Obsidian writes a ``---`` fenced YAML block at the top of a note. We only need
a tiny subset - scalars, inline flow lists (``[a, b]``), block lists
(``- item``) and block scalars (``|`` literal / ``>`` folded) - so this is
parsed without a YAML dependency.

Block scalars let a value span multiple lines, e.g. an inline BibTeX
bibliography::

    bibliography: |
      @book{knuth1984,
        author = {Knuth, Donald E.},
        title  = {The TeXbook},
      }
"""

from __future__ import annotations

__all__ = ["FrontmatterValue", "split_frontmatter"]

type FrontmatterValue = str | list[str]


def _strip_quotes(text: str) -> str:
    text = text.strip()
    if len(text) >= 2 and text[0] in "\"'" and text[-1] == text[0]:
        return text[1:-1]
    return text


def _parse_flow_list(text: str) -> list[str]:
    """Parse an inline ``[a, b, c]`` list into stripped, unquoted items."""
    inner = text.strip()[1:-1]
    return [_strip_quotes(item) for item in inner.split(",") if item.strip()]


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _block_scalar_header(value: str) -> tuple[str, str] | None:
    """Parse a ``|``/``>`` block-scalar header into ``(style, chomping)``.

    ``style`` is ``"|"`` (literal) or ``">"`` (folded); ``chomping`` is ``"-"``
    (strip), ``"+"`` (keep) or ``""`` (clip, the default). Returns ``None`` when
    ``value`` is an ordinary scalar that merely happens to start with ``|``/``>``
    (e.g. ``|pipe``), so those are left untouched.
    """
    if not value or value[0] not in "|>":
        return None
    style, rest = value[0], value[1:]
    chomping = ""
    if rest[:1] in ("+", "-"):
        chomping, rest = rest[0], rest[1:]
    rest = rest.strip()
    # Only a trailing comment may follow the indicator; anything else means this
    # was not a block scalar after all.
    if rest and not rest.startswith("#"):
        return None
    return style, chomping


def _consume_block(
    lines: list[str], start: int, parent_indent: int
) -> tuple[list[str], int]:
    """Collect the lines of a block scalar.

    A line belongs to the block while it is blank or indented deeper than the
    ``key:`` line. Returns the captured (raw) lines and the index of the first
    line that does not belong to the block.
    """
    block: list[str] = []
    i = start
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            block.append("")
            i += 1
            continue
        if _indent(line) <= parent_indent:
            break
        block.append(line)
        i += 1
    return block, i


def _dedent(block: list[str]) -> list[str]:
    """Strip the common leading indentation of the block's non-empty lines."""
    indents = [_indent(line) for line in block if line.strip()]
    base = min(indents) if indents else 0
    return [line[base:] if len(line) >= base else "" for line in block]


def _fold(lines: list[str]) -> str:
    """Fold a ``>`` block: single line breaks become spaces, blank lines stay.

    A run of N blank lines between paragraphs collapses to N line breaks; lines
    within a paragraph are joined with a single space.
    """
    parts: list[str] = []
    pending_blanks = 0
    started = False
    for line in lines:
        if not line.strip():
            pending_blanks += 1
            continue
        if started:
            parts.append("\n" * pending_blanks if pending_blanks else " ")
        parts.append(line)
        pending_blanks = 0
        started = True
    return "".join(parts)


def _chomp(text: str, chomping: str) -> str:
    """Apply the block-scalar trailing-newline (chomping) indicator."""
    if chomping == "-":  # strip: no trailing newline
        return text.rstrip("\n")
    if chomping == "+":  # keep: leave trailing newlines as captured
        return text
    # clip (default): a single trailing newline when there is content
    return text.rstrip("\n") + "\n" if text.strip() else ""


def _render_block(block: list[str], style: str, chomping: str) -> str:
    dedented = _dedent(block)
    text = _fold(dedented) if style == ">" else "\n".join(dedented)
    return _chomp(text, chomping)


def _parse_block(lines: list[str]) -> dict[str, FrontmatterValue]:
    meta: dict[str, FrontmatterValue] = {}
    key: str | None = None
    i = 0
    while i < len(lines):
        raw = lines[i]
        if not raw.strip():
            i += 1
            continue
        stripped = raw.strip()
        # A block-list continuation belongs to the most recent key.
        if stripped.startswith("- ") and key is not None:
            item = _strip_quotes(stripped[2:])
            existing = meta.get(key)
            if isinstance(existing, list):
                existing.append(item)
            else:
                meta[key] = [item]
            i += 1
            continue
        if ":" not in stripped:
            i += 1
            continue
        raw_key, _, value = raw.partition(":")
        key = raw_key.strip()
        value = value.strip()
        header = _block_scalar_header(value)
        if header is not None:
            block, i = _consume_block(lines, i + 1, _indent(raw))
            meta[key] = _render_block(block, *header)
            continue
        if not value:
            # Either a block list follows, or an empty scalar.
            meta[key] = ""
        elif value.startswith("[") and value.endswith("]"):
            meta[key] = _parse_flow_list(value)
        else:
            meta[key] = _strip_quotes(value)
        i += 1
    return meta


def split_frontmatter(text: str) -> tuple[dict[str, FrontmatterValue], str]:
    """Split ``text`` into (frontmatter mapping, remaining body).

    Returns an empty mapping and the unchanged text when no ``---`` fence opens
    the document.
    """
    if not text.lstrip().startswith("---"):
        return {}, text
    # Normalise to make the leading fence easy to consume.
    stripped = text.lstrip("\n")
    lines = stripped.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    end = next(
        (i for i in range(1, len(lines)) if lines[i].strip() == "---"),
        None,
    )
    if end is None:
        return {}, text
    meta = _parse_block(lines[1:end])
    body = "\n".join(lines[end + 1 :]).lstrip("\n")
    return meta, body
