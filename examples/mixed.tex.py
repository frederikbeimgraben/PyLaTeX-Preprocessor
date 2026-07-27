"""Example `.tex.py` file that mixes the Python API with Markdown.

    pytex examples/mixed.tex.py --build     # -> build/mixed.out.pdf

This example uses the Markdown converter through `Markdown` and
`IncludeMarkdown`. It also puts an HSRT colored box next to nodes that the
file builds by hand.

`IncludeMarkdown` reads its path relative to the working directory. Start
`pytex` in the repository root. From another directory PyTeX does not find
`examples/notes.md`.
"""

from pytex.commands.builtin import Section
from pytex.model.concat import Concat
from pytex.model.document import Document

from pytex_components.boxes import SuccessBox
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
