"""Static analysis of a `TeX` node tree.

Walks the document AST and reports likely problems before the source is handed
to tectonic: references to undefined labels, labels defined more than once, and
`\\includegraphics` paths that do not exist on disk.

    from pytex_analyze import analyze, Severity

    for issue in analyze(node):
        print(issue.severity, issue.message)
"""

from .analyze import Issue, Severity, analyze
from .optimize import Optimize

__all__ = ["Issue", "Optimize", "Severity", "analyze"]
