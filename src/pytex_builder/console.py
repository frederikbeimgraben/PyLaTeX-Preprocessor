"""Minimal, tectonic-style terminal output.

No emojis, no progress bars - just level-tagged lines with restrained color.
Color is disabled automatically when stderr is not a TTY or ``NO_COLOR`` is set.
"""

from __future__ import annotations

import os
import sys
from typing import Final, TextIO

__all__ = ["Console", "color_enabled"]


def color_enabled(stream: TextIO) -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("PYTEX_FORCE_COLOR"):
        return True
    return bool(getattr(stream, "isatty", lambda: False)())


class _Style:
    RESET: Final = "\033[0m"
    BOLD: Final = "\033[1m"
    DIM: Final = "\033[2m"
    RED: Final = "\033[31m"
    GREEN: Final = "\033[32m"
    YELLOW: Final = "\033[33m"
    BLUE: Final = "\033[34m"
    CYAN: Final = "\033[36m"


class Console:
    """Writes level-tagged status lines to ``stderr``."""

    def __init__(self, stream: TextIO | None = None) -> None:
        self.stream: TextIO = stream or sys.stderr
        self.color: bool = color_enabled(self.stream)

    def _paint(self, text: str, *codes: str) -> str:
        if not self.color or not codes:
            return text
        return f"{''.join(codes)}{text}{_Style.RESET}"

    def _emit(self, tag: str, message: str, *codes: str) -> None:
        prefix = self._paint(tag, _Style.BOLD, *codes)
        self.stream.write(f"{prefix} {message}\n")
        self.stream.flush()

    def step(self, message: str) -> None:
        """A high-level pipeline stage (e.g. 'Rendering', 'Compiling')."""
        self._emit("==>", message, _Style.GREEN)

    def note(self, message: str) -> None:
        self._emit("note:", message, _Style.CYAN)

    def warn(self, message: str) -> None:
        self._emit("warning:", message, _Style.YELLOW)

    def error(self, message: str) -> None:
        self._emit("error:", message, _Style.RED)

    def hint(self, message: str) -> None:
        """A follow-up suggestion attached to a preceding warning/error."""
        bullet = self._paint("    cause:", _Style.DIM)
        self.stream.write(f"{bullet} {message}\n")
        self.stream.flush()

    def detail(self, message: str) -> None:
        """An indented, dimmed continuation line."""
        self.stream.write(f"{self._paint('    ' + message, _Style.DIM)}\n")
        self.stream.flush()

    def success(self, message: str) -> None:
        self._emit("==>", message, _Style.GREEN)
