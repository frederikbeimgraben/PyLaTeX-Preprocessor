# PyTeX

PyTeX builds a LaTeX document from Python, and a type checker can check the
Python code. You build the document as a node tree of typed `TeX` nodes. Then
you render it to a rendered `.tex` file. You can also put inline Python
expressions into an existing `.tex` source. PyTeX evaluates them when it
renders the file. PyTeX needs Python 3.13 or later.

A `TeX` node is a dataclass with a `.rendered` property. Most node types are
immutable. The types `Document`, `Raw` and `IncludeImage` stay mutable. The
public API mirrors the LaTeX control sequences as PascalCase factories
(`Section`, `Bold`, `Frac`, `Title`, ...), so a document reads like the LaTeX
it renders. A node requires a package, so PyTeX assembles the preamble from
the package requirements that the body uses.

## Install

### Prebuilt binary

Each release attaches a standalone `pytex` binary for Linux, macOS and Windows.
The binary needs neither Python nor `pip`. Download one from the
[Releases](https://github.com/frederikbeimgraben/PyTeX-Preprocessor/releases)
page, make it executable, and run it.

The binary holds its own interpreter and common data packages. Those packages
are numpy, pandas, openpyxl and calamine for spreadsheets, Pillow, and PyYAML.
A document can `import` those without an install (see
[`packaging/`](packaging/)). PyTeX builds the binary on Python 3.14, so a
document can use `tex(t"...")` on a machine without Python 3.14. A build with
`--build` still needs the tectonic binary, which PyTeX downloads on first use.

### From PyPI

To get the `pytex` command everywhere, install it as an isolated tool with
[pipx](https://pipx.pypa.io/):

```sh
pipx install pytex-preprocessor
```

A plain `pip install pytex-preprocessor` also works.

For development, work in a virtualenv and make an editable install instead:

```sh
python -m venv venv && . venv/bin/activate
pip install -e .            # add [dev] for pytest, ruff, basedpyright
```

PyTeX uses these external tools. Each tool serves one feature:

- `tectonic` — compiles the rendered `.tex` file to PDF (`--build`). If the
  tectonic binary is not on `PATH`, PyTeX downloads a self-contained binary
  into `$XDG_CACHE_HOME/pytex` or `~/.cache/pytex` and reuses it.
- `inkscape` — converts an `SVG` image to PDF.
- `makeindex` (from a TeX distribution, for example TeX Live) — resolves the
  `glossaries` entries and the acronyms.

## Quick start

A `.tex.py` file is plain Python that defines the `__pytex__` node at module
level. That node holds a `TeX` node:

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

PyTeX coerces a bare string to a text node and escapes it for LaTeX.

### Template strings (Python 3.14+)

On Python 3.14, `pytex.tex` accepts a [PEP 750](https://peps.python.org/pep-0750/)
template string and builds a node tree from it. The static parts stay literal
LaTeX. For an interpolation, `tex` escapes a plain value for LaTeX, and puts a
`TeX` node into the node tree without a change. It handles a nested template
string, a list and a tuple the same way:

```py
from pytex import tex

name = "Q&A: 50%"
body = tex(t"{Bold('Heading')} — {name}")   # node spliced; name -> "Q\&A: 50\%"
```

PyTeX exports `tex` only on Python 3.14 and later. The rest of the library runs
on Python 3.13.

## The `pytex` command

PyTeX dispatches the input file by its extension:

| Extension | Handling |
| --- | --- |
| `.py` | PyTeX imports the file as a module and renders its `__pytex__` node. By convention, name the file `<doc>.tex.py`. |
| `.tex` | PyTeX wraps the file in `IncludeTeX`, evaluates each inline `pytex(...)` marker, then renders the file. By convention, name the file `<doc>.py.tex`. |
| `.md` / `.markdown` | The Markdown converter turns the file into nodes. PyTeX wraps them in a document that `--variant` picks (see below). Without `--variant`, PyTeX detects the variant. |

### Inline `pytex(...)` markers in `.tex`

Every registered factory is in scope inside a marker. The `\iffalse ... \fi`
pair is a LaTeX no-op, so LaTeX still compiles the source without PyTeX:

```tex
Today is \iffalse{pytex(Today())}\fi.
A fraction: $\iffalse{pytex(Frac("1", "2"))}\fi$.
Plain Python works too: $3^2 = \iffalse{pytex(3 ** 2)}\fi$.
```

### Options

| Flag | Default | Meaning |
| --- | --- | --- |
| `-o`, `--output` | `<build-dir>/<input>.out.tex` | path of the rendered `.tex` file |
| `-b`, `--build` | off | compile the rendered `.tex` file to PDF with the tectonic binary |
| `--build-dir DIR` | `build` | build directory for the artifacts and the tectonic output |
| `--no-shell-escape` | shell-escape on | turn shell-escape off |
| `-t`, `--tree` | off | also print the node tree of the input file in `tree` style before the render |
| `-f`, `--force` | off | skip the optimize pass and the analysis pass, and build even when PyTeX finds a problem |
| `--variant STYLE` | auto-detect | variant for a Markdown input file (`plain`, `report`, `report-makers`, `protocol`, `protocol-asta`, `protocol-stupa`) |
| `--config JSON` | none | JSON object of document-class parameters. `--config` overrides the frontmatter. |
| `--untrusted` | off (trusted) | render input from a source you do not trust through the trust policy (see [Security](#security-and-trust)) |
| `--trust-level LEVEL` | `trusted` | the trust level: `trusted`, `sandboxed`, or `untrusted` (see [Security](#security-and-trust)) |

Shell-escape is on by default, because an inline image decodes its base64
data during the compile pass. The build runs the tectonic binary, then the
makeindex step for `glossaries` and the acronyms. When the makeindex step
rebuilds an index, the build runs one more compile pass.

### Security and trust

By default the `pytex` command runs at trust level `trusted`. At that level
PyTeX imports and executes a `.py` input file. It evaluates each inline
`pytex(...)` marker of a `.tex` input file and each Markdown `eval` comment. It
also turns shell-escape on. This is code execution by design, because that is
how a PyTeX document works. **Use the default only on a document you wrote
yourself.**

If the input file comes from a source you do not trust, pass `--untrusted` (or
`--trust-level {sandboxed,untrusted}`). Both options route the build through
the `pytex_api` trust policy. The trust policy:

- refuses a `.py` or `.tex.py` input file, so PyTeX executes no Python,
- leaves each inline `pytex(...)` marker and each Markdown `eval` comment
  inert,
- forces shell-escape **off**, and rejects a package that opens a
  code-execution surface (`minted`, `shellesc`, `pythontex`, …) and every
  package off the package allowlist,
- applies the CPU, memory and output limits, and
- needs the Podman sandbox for a PDF build at both trust levels. The level
  `sandboxed` has a wider package allowlist than `untrusted`.

`--untrusted` is shorthand for `--trust-level untrusted`. The two options are
mutually exclusive. The default trust level is `trusted`, so an existing
command line does not change.

The `pytex` command prints short, color-tagged output (`==>`, `note:`,
`warning:`, `error:`) in the style of tectonic. On a failure it names the
likely cause and the log file. Set `NO_COLOR` to turn color off.

### The optimize pass and the analysis pass

Before PyTeX renders the node tree, it runs the optimize pass and then the
analysis pass. The optimize pass tidies the node tree. It flattens a nested
`Concat`, drops an empty node, and turns a whole-`Raw` LaTeX construct into a
native node. It also expands each inline `pytex(...)` marker, and turns a `Raw`
comment and `Raw` math (`\[...\]`, `\(...\)`, `$...$`) into a native node. The
optimize pass is render-equivalent. The analysis pass then runs static checks
for problems that LaTeX reports late or not at all:

- a reference (`\ref`, `\cref`, `\autoref`, ...) to a label that no node
  defines,
- a label that more than one node defines,
- an `\includegraphics` path that does not exist on disk.

A missing image is an error and stops the build. Every other issue is a
warning. To skip both passes and build anyway, pass `-f` or `--force`.

### Inspecting the node tree

`--tree` prints the node tree of the input file, then renders or builds as
usual. Use it to see how PyTeX maps an input file to nodes. A node that
requires a package carries a tag with the package name (`[+package]`):

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

`pytex` is the core package. Every other package is optional and builds on
`pytex`.

| Package | Provides |
| --- | --- |
| `pytex` | the core node model, `Document`, math, tables, graphics, and the factories for the common LaTeX packages (biblatex, cleveref, glossaries, hyperref, listings, ...). |
| `pytex_koma` | the KOMA-Script classes and commands (`Addchap`, `Minisec`, `KOMAoptions`, ...). |
| `pytex_tikz` | TikZ pictures and primitives (`TikzPicture`, `Draw`, `Node`, `Circle`, ...). |
| `pytex_components` | the components that any document can use: colored boxes (`ColoredBox` and the presets), a voting tally, a draft watermark, word-count and smart-pagebreak macros, a clickable author-year citation, and German cleveref labels. |
| `pytex_markdown` | the Markdown converter, which turns Markdown into native `TeX` nodes (see below). It holds `pytex_markdown.protocol` for a StuPa or AStA meeting protocol, and `pytex_markdown.frontmatter` for the YAML frontmatter. |
| `pytex_analyze` | the analysis pass, which runs static checks over the node tree for a dangling reference, a duplicate label and a missing image. It also holds `Optimize`, the render-equivalent optimize pass. |
| `pytex_hsrtreport` | the HSRT report document class, the title pages, the logos, and the HSRT color, font and glossary helpers. It builds on `pytex_components` and re-exports it, so an older import keeps working. |
| `pytex_protocol` | the deprecated alias for `pytex_markdown.protocol`. It stays as a re-export shim. |

## Markdown

The Markdown converter in `pytex_markdown` turns Markdown into native `TeX`
nodes. It parses the source with `marko`:

```py
from pytex_markdown import Markdown, IncludeMarkdown

body = Markdown("# Title\n\nText with **bold**, `code`, [a link](https://x).")
body = IncludeMarkdown("notes.md", base_level=-1)   # base_level=-1: # -> \chapter
```

A heading, emphasis, inline code and fenced code map to the core `pytex`
library. A list, a link, an image, a GFM table, a block quote and a thematic
break map to it too. The Markdown converter escapes the text for LaTeX. It adds
these extras to plain Markdown:

- **GitHub-style callouts** become colored boxes from `pytex_components`:
  ```md
  > [!NOTE]      -> InfoBox        > [!IMPORTANT] -> ImportantBox
  > [!TIP]       -> SuccessBox     > [!WARNING]   -> WarningBox
  ```
- **Citations** in Pandoc syntax. `[@key]` and `[@key, p. 5]` -> `\autocite`,
  `[@a; @b]` -> one combined cite, and a narrative `@key` -> `\textcite`.
- **Bibliography** from the frontmatter. The key `bibliography:` holds either
  inline BibTeX (a `|` block scalar) or a path to a `.bib` file. A report
  variant prints a numbered `\printbibliography`.
- An ASCII **math arrow** (`->`, `=>`, `<->`, ...) becomes an inline math
  arrow. The **euro sign** `€` becomes a font-independent `\euro{}`. A table
  gets more vertical space.

PyTeX registers both factories, so they also work in an inline `pytex(...)`
marker in a `.tex` input file.

### Output variants

When the `pytex` command renders a `.md` file, it wraps the converted nodes in
a document that `--variant` picks:

| Variant | Document |
| --- | --- |
| `plain` | a bare `Document`. The default document class is `article`, and `#` -> `\section`. |
| `report` | an HSRT report with a title page and a table of contents. `#` -> `\chapter`. |
| `report-makers` | a `report` with the MAKERS logo on the title page and in the footer. |
| `protocol` | a meeting protocol with no corporate design of its own. The caller names the logos with `logos` and `footer_logos`. |
| `protocol-asta` | an AStA meeting protocol. It is an HSRT report with the AStA logos. |
| `protocol-stupa` | a StuPa meeting protocol. It is an HSRT report with the StuPa logos. |

Without `--variant`, PyTeX detects the variant. Meeting-protocol frontmatter
(`gremium:` or `typ: protokoll`) picks a protocol variant. Every other input
file gets `plain`.

Document-class parameters come from the YAML frontmatter and from `--config`, a
JSON object. `--config` overrides the frontmatter. For example:

```sh
pytex notes.md --variant plain --config '{"documentclass": "scrartcl", "classoptions": ["11pt", "twocolumn"]}'
```

`classoptions` accepts a list (`"twocolumn"`, `"DIV=12"`) or a `{key: value}`
object. A variant with a title page, such as `report`, takes the title from
`title:` or from `--config`. If neither one gives a title, the variant takes
the first `#` heading, and then does not also render it as a chapter.

The report variants read more frontmatter keys. These are `author`, `abstract`,
`keywords`, the title-page `datalines` (a list of `"Label: value"` entries), and
`bibliography` (see [Markdown](#markdown)). The key `logos` names the title-page
logos, and the key `footer_logos` the logos of the page footer. Each one takes
a vendored name such as `INF` or `MAKERS`, a path to a custom image file, or
both. Without these keys, the variant supplies its own logos. The keys `abstract_heading` and `keywords_heading` rename
the default "Abstract" and "Keywords" sections.

## Converting LaTeX to PyTeX

`pytex-tex2py` turns an existing `.tex` file into an equivalent `.tex.py` file.
It reads the file and runs the optimize pass over it. The optimize pass expands
each inline `pytex(...)` marker and recognizes comments and math.
`pytex-tex2py` then serializes the result to Python that rebuilds the same node
tree:

```sh
pytex-tex2py paper.tex            # -> paper.tex.py
pytex-tex2py paper.tex -o out.py
```

The rendered `.tex` file of the new `.tex.py` file matches the original byte
for byte. A node that the serializer does not handle falls back to a literal
`Raw`, so the conversion always round-trips.

## Examples

The `examples/` directory holds one minimal input file per kind: `.tex.py`,
`.py.tex`, `.md`, a mixed file, and a full HSRT report. Run the commands from
the repository root, so the relative paths resolve:

```sh
pytex examples/document.tex.py --build
pytex examples/replacements.py.tex --build
pytex examples/notes.md --build
```

## Stability

From 1.0 on, PyTeX follows [Semantic Versioning](https://semver.org). The
public API is what each package exports through its top-level `__all__`. That
is every name you can reach as `from pytex import X`, and the same for
`pytex_koma`, `pytex_tikz`, `pytex_components`, `pytex_markdown`,
`pytex_analyze` and `pytex_hsrtreport`. A change that breaks one of those names
needs a major version bump.

The contract also covers the registry keys that an inline `pytex(...)` marker
can use. A registry key is the name of a factory, so a rename of a registered
factory is a breaking change. For that reason the `\fill` length is `Fill_len`,
which leaves the bare `Fill` registry key to the TikZ path command.

Some parts are internal, and the guarantee does not cover them. A name with a
leading underscore is internal. A module whose name starts with an underscore
is internal, for example `pytex_api._policy` and `pytex_api._compile`. A name
that a package does not list in its `__all__` is also internal. Import those at
your own risk.

The deprecated shims `pytex_protocol` and the `pytex.commands.lengths.Fill`
alias keep working and raise a `DeprecationWarning`. PyTeX may remove them in
the next major release.

## License

GNU General Public License v3.0 or later (GPL-3.0-or-later). See
[`LICENSE`](LICENSE).
