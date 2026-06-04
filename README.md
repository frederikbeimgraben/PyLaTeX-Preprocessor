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

### Prebuilt binary

Each release attaches standalone `pytex` binaries (Linux/macOS/Windows) — no
Python or `pip` needed. Download one from the
[Releases](https://github.com/frederikbeimgraben/PyTeX-Preprocessor/releases)
page, make it executable, and run it. The binary bundles its own interpreter
plus common data packages (numpy, pandas, openpyxl/calamine for spreadsheets,
Pillow, PyYAML), so documents can `import` those without installing anything;
see [`packaging/`](packaging/). It is built on Python 3.14, so documents may use
`tex(t"...")` even on machines without 3.14. (`--build` still needs `tectonic`,
which pytex downloads on first use.)

### From PyPI

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

### Template strings (Python 3.14+)

On Python 3.14, `pytex.tex` accepts a [PEP 750](https://peps.python.org/pep-0750/)
template string and builds a `TeX` tree from it. Static parts are literal LaTeX;
interpolations are LaTeX-escaped when they are plain values and spliced as-is
when they are `TeX` nodes (nested template strings and lists are handled too):

```py
from pytex import tex

name = "Q&A: 50%"
body = tex(t"{Bold('Heading')} — {name}")   # node spliced; name -> "Q\&A: 50\%"
```

`tex` is only exported on 3.14+; the rest of the library runs on 3.13.

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
| `--variant STYLE` | auto-detect | Markdown output style (`plain`, `report`, `report-makers`, `protocol-asta`, `protocol-stupa`) |
| `--config JSON` | none | JSON object of document-class params, merged over the frontmatter |
| `--untrusted` | off (trusted) | render foreign input through the trust policy (see [Security](#security-and-trust)) |
| `--trust-level LEVEL` | `trusted` | `trusted`, `sandboxed`, or `untrusted` (see [Security](#security-and-trust)) |

Shell-escape is on by default because inline images decode their base64
payloads at compile time. The build runs tectonic, then `makeindex` (for
`glossaries`/acronyms), then reruns tectonic when an index changed.

### Security and trust

By default the CLI runs in a **trusted** context: it imports and executes `.py`
inputs, evaluates `.tex` `pytex(...)` replacements and Markdown `eval`
comments, and enables shell-escape. That is code execution by design — it is
how PyTeX documents work — and is safe **only for documents you wrote
yourself**. Do not run the default CLI on a file from a source you do not
trust.

To render input from a foreign or untrusted source, pass `--untrusted` (or
`--trust-level {sandboxed,untrusted}`). These route the build through the
`pytex_api` trust policy, which:

- refuses `.py` / `.tex.py` inputs (no Python execution),
- leaves `.tex` `pytex(...)` markers and Markdown `eval` comments inert,
- forces shell-escape **off** and rejects code-/file-surface packages
  (`minted`, `shellesc`, `pythontex`, …) and anything off the package
  allowlist,
- applies CPU/memory/output resource limits, and
- for `sandboxed`, additionally requires the Podman OS sandbox for PDF builds.

`--untrusted` is shorthand for `--trust-level untrusted`. The two flags are
mutually exclusive; `trusted` is the default, so existing invocations are
unchanged.

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
| `pytex_components` | reusable, template-agnostic widgets: colored callout boxes (`ColoredBox` + presets), a voting tally, draft watermark, word-count and smart-pagebreak macros, a clickable author-year citation, German cleveref labels. |
| `pytex_markdown` | Markdown -> native `TeX` conversion (see below), including `pytex_markdown.protocol` (STUPA/AStA meeting minutes) and `pytex_markdown.frontmatter` (YAML frontmatter parsing). |
| `pytex_analyze` | static checks over the node tree (dangling refs, duplicate labels, missing images), plus `Optimize` to simplify a tree render-equivalently. |
| `pytex_hsrtreport` | HSRT report document class, title pages, logos, and HSRT colors/fonts/glossary helpers. Builds on `pytex_components` (and re-exports it for compatibility). |
| `pytex_protocol` | deprecated alias for `pytex_markdown.protocol` (kept as a re-export shim). |

## Markdown

`pytex_markdown` converts Markdown to native `TeX` nodes (via `marko`):

```py
from pytex_markdown import Markdown, IncludeMarkdown

body = Markdown("# Title\n\nText with **bold**, `code`, [a link](https://x).")
body = IncludeMarkdown("notes.md", base_level=-1)   # base_level=-1: # -> \chapter
```

Headings, emphasis, inline/fenced code, lists, links, images, GFM tables, block
quotes and thematic breaks map to the standard pytex library; text is
LaTeX-escaped. Some extras on top of plain Markdown:

- **GitHub-style callouts** become colored boxes (from `pytex_components`):
  ```md
  > [!NOTE]      -> InfoBox        > [!IMPORTANT] -> ImportantBox
  > [!TIP]       -> SuccessBox     > [!WARNING]   -> WarningBox
  ```
- **Citations** in Pandoc syntax: `[@key]` / `[@key, p. 5]` -> `\autocite`,
  `[@a; @b]` -> a combined cite, and a narrative `@key` -> `\textcite`.
- **Bibliography** from frontmatter — `bibliography:` is either inline BibTeX (a
  `|` block scalar) or a path to a `.bib` file; reports print a numbered
  `\printbibliography`.
- ASCII **math arrows** (`->`, `=>`, `<->`, ...) become inline math arrows, the
  **euro sign** `€` becomes a font-independent `\euro{}`, and tables get a bit of
  vertical breathing room.

Both factories are registered, so they work in `\iffalse{pytex(...)}\fi`
replacements in `.tex` sources too.

### Output variants

When the `pytex` command renders a `.md` file it wraps the converted nodes in a
document chosen by `--variant`:

| Variant | Document |
| --- | --- |
| `plain` | a bare `Document` (default class `article`); `#` -> `\section`. |
| `report` | an HSRT report with title page and table of contents; `#` -> `\chapter`. |
| `report-makers` | a `report` branded with the MAKERS logo (title page + footer). |
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

The report styles read further frontmatter keys: `author`, `abstract`,
`keywords`, title-page `datalines` (a list of `"Label: value"` entries),
`bibliography` (see [Markdown](#markdown)), `logos` (title-page logos — vendored
names like `INF`/`MAKERS` and/or paths to custom image files), and the labels
`abstract_heading` / `keywords_heading` to rename the default "Abstract" /
"Keywords" sections.

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

## Stability

From 1.0 the project follows [Semantic Versioning](https://semver.org). The
public API is what each package exports through its top-level `__all__`:
everything reachable as `from pytex import X` (and the same for `pytex_koma`,
`pytex_tikz`, `pytex_components`, `pytex_markdown`, `pytex_analyze`,
`pytex_hsrtreport`). Breaking those names needs a major version bump.

Also part of the contract: the registry keys exposed to `\iffalse{pytex(...)}\fi`
markers — they are the factory names, so renaming a registered factory is a
breaking change (which is why the `\fill` length is `Fill_len`, leaving the bare
`Fill` key to the TikZ path command).

Internal and not covered by the guarantee: any name with a leading underscore,
modules whose name starts with an underscore (e.g. `pytex_api._policy`,
`pytex_api._compile`), and anything not listed in a package's `__all__`. Import
those at your own risk.

Deprecated shims (`pytex_protocol`, the `pytex.commands.lengths.Fill` alias) keep
working with a `DeprecationWarning` and may be removed in the next major release.

## License

GNU General Public License v3.0 or later (GPL-3.0-or-later). See
[`LICENSE`](LICENSE).
