"""`.tex.py` example: mix the Python API with embedded Markdown.

    pytex examples/mixed.tex.py --build     # -> build/mixed.out.pdf

Shows ``Markdown`` / ``IncludeMarkdown`` and an HSRT colored box used directly
alongside hand-built nodes.
"""

from pytex.commands.builtin import Section
from pytex.model.concat import Concat
from pytex.model.document import Document

from pytex_hsrtreport.boxes import SuccessBox
from pytex_markdown import IncludeMarkdown, Markdown

__pytex__ = Document(
    body=Concat(
        Section("Inline Markdown"),
        Markdown("Convert a **string** of Markdown with a `code` span."),
        Section("A box, built directly"),
        SuccessBox("This colored box comes straight from the HSRT report module."),
        Section("An included Markdown file"),
        IncludeMarkdown("examples/notes.md", base_level=1),
    ),
)
