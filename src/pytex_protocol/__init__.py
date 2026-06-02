"""STUPA/AStA meeting-protocol rendering, built on top of ``pytex_hsrtreport``.

Write the minutes in Obsidian-flavoured Markdown - YAML frontmatter for the
meeting header, ``> [!beschluss]`` / ``> [!abstimmung]`` / ``> [!aufgabe]``
callouts and inline ``{{shortcodes}}`` for the protocol-specific bits - and
render it to a PDF that matches the HSRTReport look.

    from pytex_protocol import IncludeProtocol
    __pytex__ = IncludeProtocol("sitzung.md")
"""

from .convert import ProtocolConverter
from .document import IncludeProtocol, Protocol, build_protocol, render_protocol
from .entries import ActionItem, Deadline, Decision, Timestamp, Vote
from .frontmatter import split_frontmatter
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
