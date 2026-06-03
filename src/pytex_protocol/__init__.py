"""Deprecated alias for :mod:`pytex_markdown.protocol`.

``pytex_protocol`` was merged into ``pytex_markdown``: the generic
frontmatter parser moved to :mod:`pytex_markdown.frontmatter` and the
meeting-protocol rendering to :mod:`pytex_markdown.protocol`. This package
re-exports that public API so existing imports keep working; prefer the new
locations.
"""

from __future__ import annotations

import warnings

from pytex_markdown.frontmatter import split_frontmatter
from pytex_markdown.protocol import (
    ActionItem,
    Deadline,
    Decision,
    IncludeProtocol,
    Protocol,
    ProtocolConverter,
    ProtocolHeader,
    SignatureLines,
    Timestamp,
    Vote,
    build_protocol,
    expand_inline_shortcodes,
    expand_shortcode,
    header_from_meta,
    render_protocol,
    signature_block_from_meta,
)

warnings.warn(
    "pytex_protocol is deprecated; import from pytex_markdown.protocol "
    "(and pytex_markdown.frontmatter) instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "ActionItem",
    "Deadline",
    "Decision",
    "IncludeProtocol",
    "Protocol",
    "ProtocolConverter",
    "ProtocolHeader",
    "SignatureLines",
    "Timestamp",
    "Vote",
    "build_protocol",
    "expand_inline_shortcodes",
    "expand_shortcode",
    "header_from_meta",
    "render_protocol",
    "signature_block_from_meta",
    "split_frontmatter",
]
