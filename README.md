# PyTeX

Type-safe LaTeX document generation with Python. Build a document as a tree of
typed `TeX` nodes and render it to a `.tex` file, or drop inline Python
expressions into an existing `.tex` source and have them evaluated at render
time. Requires Python 3.13+.

A `TeX` node is an immutable dataclass with a `.rendered` property. The public
API mirrors LaTeX control sequences as PascalCase factories (`Section`,
`Bold`, `Frac`, `Title`, ...), so a document reads like the LaTeX it produces
while staying checkable by a type checker. Nodes track their package
requirements, so the preamble is assembled automatically from what the body
uses.

## Install

To use the `pytex` command anywhere, install it as an isolated tool with
[pipx](https://pipx.pypa.io/):

```sh
pipx install pytex-preprocessor
```

It is also available via plain `pip install pytex-preprocessor`.

For development, work in a virtualenv with an editable install instead:

```sh
python -m venv venv && . venv/bin/activate
pip install -e .            # add [dev] for pytest, ruff, basedpyright
```

External tools, each needed only for the matching feature:

- `tectonic` — compile to PDF (`--build`). If not on `PATH`, the build
  downloads a self-contained binary into a temp folder and reuses it.
- `inkscape` — `SVG` image conversion.
- `makeindex` (from a TeX distribution, e.g. TeX Live) — resolve
  glossaries/acronyms.

## Quick start

A `.tex.py` file is plain Python exposing a module-level `__pytex__` that holds
a `TeX` node:

```py
from pytex.commands.builtin import Bold, Emph, Section, Title, MakeTitle
from pytex.model.concat import Concat
from pytex.model.document import Document
from pytex.model.math import DisplayMath, Frac

__pytex__ = Document(
    preamble=Title("PyTeX Example"),
    body=Concat(
        MakeTitle(),
        Section("Text"),
        "A paragraph with ", Bold("bold"), " and ", Emph("emphasised"), " words.",
        Section("Math"),
        DisplayMath(Concat("x = ", Frac("-b", "2a"))),
    ),
)
```

```sh
pytex example.tex.py          # render -> build/example.out.tex
pytex example.tex.py --build  # render + compile -> build/example.out.pdf
```

Bare strings are coerced to text nodes and LaTeX-escaped.

## The `pytex` command

The input file is dispatched by extension:

| Extension | Handling |
| --- | --- |
| `.py` | imported as a module; its `__pytex__` node is rendered. Convention: name it `<doc>.tex.py`. |
| `.tex` | wrapped in `IncludeTeX`; inline `\iffalse{pytex(...)}\fi` markers are evaluated, then rendered. Convention: `<doc>.py.tex`. |
| `.md` / `.markdown` | converted to nodes and wrapped in a document according to `--variant` (see below). Without `--variant` the style is auto-detected. |

### Inline replacements in `.tex`

Any registered factory is in scope inside a marker. The `\iffalse ... \fi` pair
is a LaTeX no-op, so the source still compiles as-is without PyTeX:

```tex
Today is \iffalse{pytex(Today())}\fi.
A fraction: $\iffalse{pytex(Frac("1", "2"))}\fi$.
Plain Python works too: $3^2 = \iffalse{pytex(3 ** 2)}\fi$.
```

### Options

| Flag | Default | Meaning |
| --- | --- | --- |
| `-o`, `--output` | `<build-dir>/<input>.out.tex` | rendered LaTeX output path |
| `-b`, `--build` | off | compile the rendered `.tex` to PDF with tectonic |
| `--build-dir DIR` | `build` | directory for artifacts and tectonic output |
| `--no-shell-escape` | shell-escape on | disable shell-escape |
| `-t`, `--tree` | off | also print the input's `TeX`-node tree (`tree`-style) before rendering/building |
| `-f`, `--force` | off | skip the optimize + analysis pass and build even if problems are found |
| `--variant STYLE` | auto-detect | Markdown output style (`plain`, `report`, `protocol-asta`, `protocol-stupa`) |
| `--config JSON` | none | JSON object of document-class params, merged over the frontmatter |

Shell-escape is on by default because inline images decode their base64
payloads at compile time. The build runs tectonic, then `makeindex` (for
`glossaries`/acronyms), then reruns tectonic when an index changed.

Output is minimal and color-tagged (`==>`, `note:`, `warning:`, `error:`),
following tectonic's style; on failure it points at the likely cause and the
log file. Set `NO_COLOR` to disable color.

### Pre-flight optimize + analysis

Before rendering, the builder runs two render-equivalent passes over the node
tree. First `Optimize` tidies the tree (flatten nested `Concat`s, drop empty
nodes, turn whole-`Raw` LaTeX constructs into native nodes) without changing
the output (it also expands inline `pytex(...)` markers and turns `Raw`
comments and math — `\[...\]`, `\(...\)`, `$...$` — into native nodes). Then
`pytex_analyze` checks for problems that LaTeX would only surface later (or
silently):

- references (`\ref`, `\cref`, `\autoref`, ...) to a label that is never
  defined,
- labels defined more than once,
- `\includegraphics` paths that do not exist on disk.

Missing-image issues are errors and abort the build; the rest are warnings.
Pass `-f`/`--force` to skip both passes and build regardless.

### Inspecting the node tree

`--tree` prints the parsed `TeX`-node tree (then renders/builds as usual),
useful for debugging how an input maps to nodes. Nodes that require a package
are tagged with it (`[+package]`):

```
$ pytex example.tex.py --tree
Document (article)
├── ControlSequence \title
│   └── Parameter { }
│       └── Raw "PyTeX Example"
└── Concat
    ├── ControlSequence \maketitle
    ├── ControlSequence \cref [+cleveref]
    └── ...
```

## Packages

`pytex` is the core; the rest are optional and build on it.

| Package | Provides |
| --- | --- |
| `pytex` | core node model, `Document`, math, tables, graphics, and factories for the common LaTeX packages (biblatex, cleveref, glossaries, hyperref, listings, ...). |
| `pytex_koma` | KOMA-Script classes and commands (`Addchap`, `Minisec`, `KOMAoptions`, ...). |
| `pytex_tikz` | TikZ pictures and primitives (`TikzPicture`, `Draw`, `Node`, `Circle`, ...). |
| `pytex_markdown` | Markdown -> native `TeX` conversion (see below). |
| `pytex_analyze` | static checks over the node tree (dangling refs, duplicate labels, missing images), plus `Optimize` to simplify a tree render-equivalently. |
| `pytex_hsrtreport` | HSRT report document class, colored callout boxes, title pages, glossary/citation helpers. |
| `pytex_protocol` | STUPA/AStA meeting minutes from Markdown, built on `pytex_hsrtreport`. |

## Markdown

`pytex_markdown` converts Markdown to native `TeX` nodes (via `marko`):

```py
from pytex_markdown import Markdown, IncludeMarkdown

body = Markdown("# Title\n\nText with **bold**, `code`, [a link](https://x).")
body = IncludeMarkdown("notes.md", base_level=-1)   # base_level=-1: # -> \chapter
```

Headings, emphasis, inline/fenced code, lists, links, images, block quotes and
thematic breaks map to the standard pytex library; text is LaTeX-escaped.
GitHub-style callouts become HSRT colored boxes (so the module depends on
`pytex_hsrtreport`):

```md
> [!NOTE]      -> InfoBox        > [!IMPORTANT] -> ImportantBox
> [!TIP]       -> SuccessBox     > [!WARNING]   -> WarningBox
```

Both factories are registered, so they work in `\iffalse{pytex(...)}\fi`
replacements in `.tex` sources too.

### Output variants

When the `pytex` command renders a `.md` file it wraps the converted nodes in a
document chosen by `--variant`:

| Variant | Document |
| --- | --- |
| `plain` | a bare `Document` (default class `article`); `#` -> `\section`. |
| `report` | an HSRT report with title page and table of contents; `#` -> `\chapter`. |
| `protocol-asta` | an AStA meeting protocol (HSRT report, AStA logos). |
| `protocol-stupa` | a StuPa meeting protocol (HSRT report, StuPa logos). |

Without `--variant`, protocol frontmatter (`gremium:` or `typ: protokoll`) picks
a protocol style and everything else falls back to `plain`.

Document-class parameters come from the YAML frontmatter and from `--config`
(a JSON object that overrides the frontmatter), e.g.:

```sh
pytex notes.md --variant plain --config '{"documentclass": "scrartcl", "classoptions": ["11pt", "twocolumn"]}'
```

`classoptions` accepts a list (`"twocolumn"`, `"DIV=12"`) or a `{key: value}`
object. For styles with a title page (`report`), the title is taken from
`title:`/`--config` if given, otherwise from the first `#` heading (which is then
not also rendered as a chapter).

## Converting LaTeX to PyTeX

`pytex-tex2py` turns an existing `.tex` file into an equivalent `.tex.py`
source. It reads the file, runs `Optimize` over it (expanding inline
`pytex(...)` markers and recognising comments and math), and serialises the
result to Python that rebuilds the same tree:

```sh
pytex-tex2py paper.tex            # -> paper.tex.py
pytex-tex2py paper.tex -o out.py
```

Rendering the generated `.tex.py` reproduces the original output byte-for-byte;
nodes the serialiser does not special-case fall back to a literal `Raw`, so the
conversion always round-trips.

## Examples

See `examples/` for one minimal input per kind (`.tex.py`, `.py.tex`, `.md`,
mixed, and a full HSRT report). Run from the repository root so relative paths
resolve:

```sh
pytex examples/document.tex.py --build
pytex examples/replacements.py.tex --build
pytex examples/notes.md --build
```
