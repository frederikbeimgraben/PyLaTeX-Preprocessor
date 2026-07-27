# Examples

This directory holds small input files for each kind that the `pytex` command
accepts. PyTeX writes the rendered `.tex` file into the build directory. Add
`--build` to also compile a PDF into the same directory. The default build
directory is `build/`.

| File | Kind | Feature |
| --- | --- | --- |
| `document.tex.py` | `.tex.py` | a `Document` made with the Python API |
| `replacements.py.tex` | `.py.tex` | a LaTeX file with inline `pytex(...)` markers, written as `\iffalse{pytex(...)}\fi` |
| `notes.md` | `.md` | Markdown -> node tree, with GitHub-style callouts |
| `report.md` | `.md` | `--variant report`: frontmatter fields, tables, code, arrows, an image |
| `mixed.tex.py` | `.tex.py` | Python nodes, `Markdown`, and a colored box in one document |
| `hsrtreport.tex.py` | `.tex.py` | the full `HSRTReport` document class, with chapters and colored boxes |
| `templatestring.tex.py` | `.tex.py` | `tex(t"...")` template strings (needs Python 3.14) |
| `hsrtreport-tstrings.tex.py` | `.tex.py` | `hsrtreport.tex.py` rebuilt with `tex(t"...")` (needs Python 3.14) |

```sh
pytex examples/document.tex.py --build
pytex examples/replacements.py.tex --build
pytex examples/notes.md --build
pytex examples/report.md --variant report --build
pytex examples/mixed.tex.py --build
pytex examples/hsrtreport.tex.py --build   # needs biber (biblatex)
pytex examples/templatestring.tex.py --build   # needs Python 3.14 (or a binary)
pytex examples/hsrtreport-tstrings.tex.py --build   # needs Python 3.14 + biber
```

`--build` needs the tectonic binary. PyTeX first looks for the tectonic binary
on `PATH`. PyTeX then looks in its own cache. If neither place holds the
tectonic binary, PyTeX downloads it into the cache. The HSRT report examples
use the bundled fonts. The build writes those fonts into the build directory.

Start `pytex` in the repository root. From another directory PyTeX does not
find the relative paths, such as the `examples/notes.md` that `mixed.tex.py`
includes.
