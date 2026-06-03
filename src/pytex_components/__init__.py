"""Reusable, template-agnostic document components.

These widgets and preamble helpers carry no HSRT branding and depend only on
the core ``pytex`` library, so any document or report style can use them:

* :class:`~pytex_components.boxes.ColoredBox` and its presets (info / success /
  warning / important / discussion / custom) — nested-aware coloured callouts.
* :class:`~pytex_components.voting.VotingResults` — a yes/no/abstain tally box.
* draft watermark, word-count macros, conditional/​smart page breaks.
* :func:`~pytex_components.citations.Fcite` — a clickable author-year citation.
* :func:`~pytex_components.cleveref_names.GermanCrefNames` — German cleveref labels.

``pytex_hsrtreport`` re-exports these for backwards compatibility.
"""

from .boxes import (
    ColoredBox,
    CustomBox,
    DiscussionBox,
    ImportantBox,
    InfoBox,
    SuccessBox,
    WarningBox,
)
from .citations import Fcite
from .cleveref_names import GermanCrefNames
from .pagebreak import (
    Conditionalpagebreak,
    Critical,
    Keeptogether,
    Smartsection,
    Smartsubsection,
)
from .voting import VotingResults
from .watermark import DraftWatermark, WatermarkCounter, WatermarkPackages
from .wordcount import WordcountCommands

__all__ = [
    "ColoredBox",
    "Conditionalpagebreak",
    "Critical",
    "CustomBox",
    "DiscussionBox",
    "DraftWatermark",
    "Fcite",
    "GermanCrefNames",
    "ImportantBox",
    "InfoBox",
    "Keeptogether",
    "Smartsection",
    "Smartsubsection",
    "SuccessBox",
    "VotingResults",
    "WarningBox",
    "WatermarkCounter",
    "WatermarkPackages",
    "WordcountCommands",
]
