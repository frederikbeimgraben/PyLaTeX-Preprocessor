# Standalone binary

A single-file `pytex` executable built with [PyInstaller](https://pyinstaller.org/).
It bundles its own Python interpreter, the pytex packages (with their data —
HSRT fonts/logos/tex), and the extra packages in [`bundle.toml`](bundle.toml),
so a user needs neither Python nor `pip` — just the binary (and `tectonic` for
`--build`, which pytex downloads on first use).

## Why the bundle list

The binary runs `.tex.py` files and `pytex(...)` markers inside its **own**
frozen interpreter, which cannot see the user's `site-packages`. Anything a
document might `import` must be baked in. `bundle.toml` lists those packages:

- `requirements` — pip names installed into the build environment.
- `collect` — the *import* names PyInstaller pulls in wholesale (these differ
  from the pip name for some packages: `Pillow` → `PIL`, `PyYAML` → `yaml`,
  `python-calamine` → `python_calamine`).

Add a package to both lists to make it importable from documents.

## Build locally

Use a throwaway virtualenv — the build installs PyInstaller and every bundle
requirement into the active environment:

```sh
python -m venv /tmp/pytex-build && . /tmp/pytex-build/bin/activate
pip install -e .            # pytex itself
python packaging/build.py   # -> dist/pytex
./dist/pytex --version
```

Built on Python 3.14, the binary's interpreter is 3.14, so documents may use
`tex(t"...")` / t-strings even on machines without 3.14 installed.

## CI

The `binaries` job in [`.github/workflows/release.yml`](../.github/workflows/release.yml)
builds one binary per OS (Linux/macOS/Windows) on a tag push, smoke-tests it
(runs `--version`, renders an example, and renders a document that imports a
bundled package), and attaches the binaries to the GitHub Release.
