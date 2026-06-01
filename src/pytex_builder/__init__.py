"""Build tooling for PyTeX: render ``.py``/``.tex`` sources and compile PDFs.

Exposes the ``pytex`` console script via :func:`pytex_builder.build.main`.
"""

from .build import main

__all__ = ["main"]
