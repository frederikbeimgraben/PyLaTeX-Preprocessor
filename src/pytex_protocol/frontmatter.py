"""Minimal YAML-frontmatter splitter for protocol Markdown files.

Obsidian writes a ``---`` fenced YAML block at the top of a note. We only need
a tiny subset - scalars, inline flow lists (``[a, b]``) and block lists
(``- item``) - so this is parsed without a YAML dependency.
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


def _parse_block(lines: list[str]) -> dict[str, FrontmatterValue]:
    meta: dict[str, FrontmatterValue] = {}
    key: str | None = None
    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            continue
        # A block-list continuation belongs to the most recent key.
        if line.lstrip().startswith("- ") and key is not None:
            item = _strip_quotes(line.lstrip()[2:])
            existing = meta.get(key)
            if isinstance(existing, list):
                existing.append(item)
            else:
                meta[key] = [item]
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if not value:
            # Either a block list follows, or an empty scalar.
            meta[key] = ""
        elif value.startswith("[") and value.endswith("]"):
            meta[key] = _parse_flow_list(value)
        else:
            meta[key] = _strip_quotes(value)
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
