# Examples

Minimal inputs for each kind the `pytex` builder accepts. Render to `.tex`, or
add `--build` to compile a PDF into `build/`.

| File | Kind | Feature |
| --- | --- | --- |
| `document.tex.py` | `.tex.py` | build a `Document` with the Python API |
| `replacements.py.tex` | `.py.tex` | LaTeX file with inline `\iffalse{pytex(...)}\fi` markers |
| `notes.md` | `.md` | Markdown -> PyTeX, including callouts |
| `mixed.tex.py` | `.tex.py` | mix Python nodes, `Markdown`, and an HSRT box |

```sh
pytex examples/document.tex.py --build
pytex examples/replacements.py.tex --build
pytex examples/notes.md --build
pytex examples/mixed.tex.py --build
```

`--build` downloads tectonic on first use; callouts/boxes need the bundled
fonts. Run from the repository root so relative paths (e.g. the included
`notes.md`) resolve.
