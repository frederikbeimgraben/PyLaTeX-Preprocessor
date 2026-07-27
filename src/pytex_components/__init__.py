"""Document components that any document class can use.

These components carry no HSRT branding. In Python they import only the core
`pytex` package, so any document or report style can use them. Read the note
below for the LaTeX side.

* `ColoredBox` and its presets. The presets are `InfoBox`, `SuccessBox`,
  `WarningBox`, `ImportantBox`, `DiscussionBox` and `CustomBox`. Each one
  renders a colored box that knows its own nesting depth.
* `VotingResults`, a box that shows a yes, no and abstain tally.
* `DraftWatermark`, `WatermarkCounter` and `WatermarkPackages` for a draft
  watermark.
* `WordcountCommands` for the word-count macros.
* `Conditionalpagebreak`, `Keeptogether`, `Critical`, `Smartsection` and
  `Smartsubsection` for page breaks.
* `Fcite`, a clickable citation that shows the author and the year.
* `GermanCrefNames`, the German cleveref labels.

`pytex_hsrtreport` re-exports these names, so older imports keep working.

Note:
    `VotingResults` and `DiscussionBox` name the xcolor colors
    `britishracinggreen`, `eggplant` and `hanblue`. Only
    `pytex_hsrtreport.colors` defines them. A document that does not load
    those color definitions fails to compile.

    The page-break components use `\\needspace`, but they do not require the
    `needspace` package. The document must load that package itself.
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
