"""Build tools for PyTeX: render an input file, then compile it to PDF.

This package provides the `pytex` command through `pytex_builder.build.main`.
"""

from .build import main

__all__ = ["main"]
