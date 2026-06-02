# Examples

Minimal inputs for each kind the `pytex` builder accepts. Render to `.tex`, or
add `--build` to compile a PDF into `build/`.

| File | Kind | Feature |
| --- | --- | --- |
| `document.tex.py` | `.tex.py` | build a `Document` with the Python API |
| `replacements.py.tex` | `.py.tex` | LaTeX file with inline `\iffalse{pytex(...)}\fi` markers |
| `notes.md` | `.md` | Markdown -> PyTeX, including callouts |
| `mixed.tex.py` | `.tex.py` | mix Python nodes, `Markdown`, and an HSRT box |
| `hsrtreport.tex.py` | `.tex.py` | full HSRT report class (chapters, callout boxes) |
| `templatestring.tex.py` | `.tex.py` | `tex(t"...")` template strings (needs Python 3.14) |
| `hsrtreport-tstrings.tex.py` | `.tex.py` | `hsrtreport.tex.py` rebuilt with `tex(t"...")` (needs Python 3.14) |

```sh
pytex examples/document.tex.py --build
pytex examples/replacements.py.tex --build
pytex examples/notes.md --build
pytex examples/mixed.tex.py --build
pytex examples/hsrtreport.tex.py --build   # needs biber (biblatex)
pytex examples/templatestring.tex.py --build   # needs Python 3.14 (or a binary)
pytex examples/hsrtreport-tstrings.tex.py --build   # needs Python 3.14 + biber
```

`--build` downloads tectonic on first use; callouts/boxes need the bundled
fonts. Run from the repository root so relative paths (e.g. the included
`notes.md`) resolve.
