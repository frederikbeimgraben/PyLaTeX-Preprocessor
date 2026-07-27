"""LaTeX text escaping, re-exported from the `pytex` core.

The one implementation lives in `pytex.helpers.sanitize`. The Markdown
converter and `Sanitize` use the same escape rules.
"""

from __future__ import annotations

from pytex.helpers.sanitize import escape_latex

__all__ = ["escape_latex"]
