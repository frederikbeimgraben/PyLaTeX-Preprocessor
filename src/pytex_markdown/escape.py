"""LaTeX text escaping (re-exported from pytex core).

The canonical implementation lives in :mod:`pytex.helpers.sanitize` so the
markdown converter and :func:`pytex.helpers.sanitize.Sanitize` stay in sync.
"""

from __future__ import annotations

from pytex.helpers.sanitize import escape_latex

__all__ = ["escape_latex"]
