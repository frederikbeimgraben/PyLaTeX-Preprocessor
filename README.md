# pytex

## Install

```sh
python -m venv venv && . venv/bin/activate
pip install -e .            # add [dev] for pytest
```

`SVG` conversion needs `inkscape`. Compiling to PDF needs `tectonic` — if it
is not on `PATH`, `pytex --build` downloads a self-contained binary into a
temp folder and reuses it on later runs. Resolving glossaries/acronyms needs
`makeindex` from a TeX distribution (e.g. TeX Live).

## The `pytex` command

```sh
pytex example.tex.py          # render -> example.out.tex
pytex example.tex.py --build  # render + compile -> build/example.out.pdf
```

The input is either:

- a `.py` file exposing a module-level `__pytex__` variable that is a `TeX`
  node (e.g. a `Document`) — it is rendered, or
- a `.tex` file — wrapped in `IncludeTeX` (so `\iffalse pytex(...) \fi`
  replacements are evaluated) and rendered.

### Options

| Flag | Default | Meaning |
| --- | --- | --- |
| `-o`, `--output` | `<input>.out.tex` | rendered LaTeX output path |
| `-b`, `--build` | off | compile the rendered `.tex` to PDF with tectonic |
| `--build-dir DIR` | `build` | directory for artifacts and tectonic output |
| `--no-shell-escape` | shell-escape on | disable shell-escape |

Shell-escape is enabled by default because inline images decode their base64
payloads at compile time. The build runs tectonic, then `makeindex` (for
`glossaries`/acronyms), then reruns tectonic when an index changed.

Output is minimal and color-tagged (`==>`, `note:`, `warning:`, `error:`),
following tectonic's style; on failure it points at the likely cause and the
log file. Set `NO_COLOR` to disable color.
