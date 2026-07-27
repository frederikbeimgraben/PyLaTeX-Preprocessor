"""The analysis pass, which runs static checks over a `TeX` node tree.

The pass walks the node tree and reports likely problems before the tectonic
binary compiles the rendered `.tex` file. It finds references to undefined
labels, labels defined more than once, and `\\includegraphics` paths that do
not exist on disk.

Example:
    from pytex_analyze import analyze

    for issue in analyze(node):
        print(issue.severity, issue.message)
"""

from .analyze import Issue, Severity, analyze
from .optimize import Optimize

__all__ = ["Issue", "Optimize", "Severity", "analyze"]
