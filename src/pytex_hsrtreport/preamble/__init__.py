"""Per-domain preamble builders for the HSRT report.

Each submodule returns a single :class:`pytex.TeX` node that emits one
logical section of the original ``HSRTReport.cls`` preamble. ``document.py``
composes them in order.
"""

from .cleveref import CREFNAMES, CleverefBlock
from .glossary import GlossarySettingsBlock
from .hyperref import HyperrefBlock
from .imports import PACKAGES_WITH_OPTIONS, ImportsBlock
from .lifecycle import AtBeginDocumentBlock, AtEndDocumentBlock
from .page_setup import PageSetupBlock
from .pagebreaks import PagebreaksBlock
from .sections import SectionsBlock
from .toc import TocConfigBlock
from .typography import TypographyBlock

__all__ = [
    "PACKAGES_WITH_OPTIONS",
    "ImportsBlock",
    "HyperrefBlock",
    "SectionsBlock",
    "TypographyBlock",
    "PagebreaksBlock",
    "TocConfigBlock",
    "CREFNAMES",
    "CleverefBlock",
    "GlossarySettingsBlock",
    "PageSetupBlock",
    "AtBeginDocumentBlock",
    "AtEndDocumentBlock",
]
