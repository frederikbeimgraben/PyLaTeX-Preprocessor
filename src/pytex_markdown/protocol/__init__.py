"""Meeting protocol rendering for StuPa and AStA, built on `pytex_hsrtreport`.

Write the meeting protocol in Obsidian-flavored Markdown. The YAML frontmatter
holds the meeting header. The `> [!beschluss]`, `> [!abstimmung]` and
`> [!aufgabe]` callouts and the inline `{{shortcodes}}` hold the
protocol-specific parts. The build then renders the `.tex` file and compiles it
to a PDF with the HSRTReport look.

    from pytex_markdown.protocol import IncludeProtocol
    __pytex__ = IncludeProtocol("sitzung.md")

The deprecated `pytex_protocol` package re-exports the public API of this
module.
"""

from ..frontmatter import split_frontmatter
from .convert import ProtocolConverter
from .document import IncludeProtocol, Protocol, build_protocol, render_protocol
from .entries import ActionItem, Deadline, Decision, Timestamp, Vote
from .header import ProtocolHeader, header_from_meta
from .shortcodes import expand_inline_shortcodes, expand_shortcode
from .signatures import SignatureLines, signature_block_from_meta

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
