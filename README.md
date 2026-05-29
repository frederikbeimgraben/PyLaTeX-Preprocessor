# pytex

Type-safe LaTeX generation in Python. You build a document as a tree of `TeX`
objects and call `.serialize()` to get LaTeX. A `.pytex` file is just Python that
defines a `__pytex__` document.

Three packages live under `src/`:

- `pytex` — core model and the standard LaTeX library (text, sections, math,
  figures, tables, environments, references, glossaries, listings, markdown,
  SVG, file inclusion).
- `pytex_komascript` — KOMA-Script classes (`scrartcl`/`scrreprt`/`scrbook`),
  fonts, type area, `scrlayer-scrpage` headers/footers, matter divisions.
- `pytex_hsrtreport` — the HSRT report layout (Reutlingen University) rebuilt on
  the two above. All class logic (variant logos, glossary/bibliography toggles,
  word count) runs in Python; the output is a plain `scrbook` document plus the
  full preamble.

## Install

```sh
python -m venv venv && . venv/bin/activate
pip install -e .            # add [dev] for pytest
```

`SVG` conversion needs `inkscape`; compiling to PDF needs `tectonic`.

## Build a document

```sh
build-pytex example.pytex            # -> example.tex
build-pytex example.pytex --compile  # -> example.pdf (tectonic)
./build.sh example.pytex             # build + compile + open
```

`--compile` creates a `build/` directory in the working directory; any `SVG`
nodes are rendered to PDF there before serialization.

## Core

```python
from pytex import Document, Group, Section, Raw, Bold

__pytex__ = Document(
    document_class="article",
    title="Hello",
    content=Group(Section(Raw("Intro")), Bold(Raw("bold text"))),
)
```

`Raw(content, escape_spaces=True, namespace=None)` holds literal text. Strings
passed to most constructors are coerced to `Raw`.

### Inline Python escapes

Inside `Raw` and `IncludeTeX`, two escape forms evaluate a Python expression at
serialization time and substitute the result (`str` or any `TeX`):

```
%{ pytex (EXPR) }%
\iffalse{ pytex (EXPR) }\fi
```

The namespace contains the public `pytex` exports and builtins; pass extra
objects via `namespace={...}`. `IncludeTeX(path)` reads the file, runs the
escapes, and inlines the result (falling back to `\input` if the file is
absent).

### SVG

```python
from pytex import SVG
SVG(file="diagram.svg", width="8cm")   # or SVG(xml="<svg .../>")
```

Serializes as `\includegraphics` of an Inkscape-converted PDF in `build/`.

## HSRT report

```sh
build-pytex hsrtreport_example.pytex --compile
```

See `hsrtreport_example.pytex` for a full document: title page, glossary and
acronyms, info/warning boxes, a code listing, voting results, and an automatic
word count.

```python
from pytex_hsrtreport import HSRTReport, InfoBox

doc = HSRTReport(
    content=...,
    title="...", author="...",
    variant="INF_meti",            # INF_meti/mki/huc, STUPA, ASTA, ECHO
    toc=True, wordcount=True,
    glossary=..., acronyms=..., bibliography="Main.bib",
    assets_path="HSRTReport-Template/src/HSRTReport",
)
```

`variant` picks the default logo set; `logos=` overrides it. Footer logos are
off by default (`footer_logos=True` to enable). Glossary and acronym lists need
a `makeindex`-capable build; Tectonic alone won't generate them.

`pytex_hsrtreport.Markdown` parses Markdown with GitHub-style callouts
(`> [!INFO]`, `> [!WARNING]`, ...) mapped to the info boxes and fenced code
mapped to language listings.

## Tests

```sh
pytest
```
