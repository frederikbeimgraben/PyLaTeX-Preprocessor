"""The deprecated alias for `pytex_markdown.protocol`.

PyTeX merged `pytex_protocol` into `pytex_markdown`. The general frontmatter
parser moved to `pytex_markdown.frontmatter`. The meeting protocol code moved
to `pytex_markdown.protocol`.

This package re-exports the public names from both new places, so an older
import keeps working. This package issues a `DeprecationWarning` on import.
Import from the new places instead.
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
    "pytex_protocol is deprecated; import from pytex_markdown.protocol"
    + " (and pytex_markdown.frontmatter) instead.",
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
