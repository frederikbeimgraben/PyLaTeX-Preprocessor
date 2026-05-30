"""Per-domain preamble builders for the HSRT report.

Each submodule returns a single :class:`pytex.TeX` node that emits one
logical section of the original ``HSRTReport.cls`` preamble. ``document.py``
composes them in order.
"""

from .cleveref import CREFNAMES, cleveref_block
from .glossary import glossary_settings_block
from .hyperref import hyperref_block
from .imports import IMPORTS_PACKAGES, imports_block
from .lifecycle import at_begin_document_block, at_end_document_block
from .page_setup import page_setup_block
from .pagebreaks import pagebreaks_block
from .sections import sections_block
from .toc import toc_config_block
from .typography import typography_block

__all__ = [
    "IMPORTS_PACKAGES",
    "imports_block",
    "hyperref_block",
    "sections_block",
    "typography_block",
    "pagebreaks_block",
    "toc_config_block",
    "CREFNAMES",
    "cleveref_block",
    "glossary_settings_block",
    "page_setup_block",
    "at_begin_document_block",
    "at_end_document_block",
]
