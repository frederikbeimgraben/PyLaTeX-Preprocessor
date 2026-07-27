# Standalone binary

[PyInstaller](https://pyinstaller.org/) builds a single-file `pytex`
executable. It bundles its own Python interpreter, the PyTeX packages with
their data, and the extra packages in [`bundle.toml`](bundle.toml). The package
data holds the HSRT fonts, logos and tex files. A user needs only the binary,
not Python and not `pip`. PyTeX needs the tectonic binary for `--build`. PyTeX
downloads the tectonic binary on first use.

## Why the bundle list

The binary runs a `.tex.py` file and an inline `pytex(...)` marker inside its
**own** frozen interpreter. That interpreter cannot see the `site-packages` of
the user. The build must include every package that a document can `import`.
`bundle.toml` lists those packages:

- `requirements` — the pip names. The build installs them into the build
  environment.
- `collect` — the *import* names that PyInstaller collects in full. The two
  names differ for some packages. `Pillow` imports as `PIL`, `PyYAML` imports
  as `yaml`, and `python-calamine` imports as `python_calamine`.

To make a package importable from a document, add the package to both lists.

## Build locally

Use a throwaway virtualenv. The build installs PyInstaller and every bundle
requirement into the active environment.

```sh
python -m venv /tmp/pytex-build && . /tmp/pytex-build/bin/activate
pip install -e .            # pytex itself
python packaging/build.py   # -> dist/pytex
./dist/pytex --version
```

If you build with Python 3.14, the interpreter inside the binary is also 3.14.
A document can then use `tex(t"...")` and t-strings on a machine that has no
Python 3.14.

## CI

A push of a version tag starts the workflow in
[`.github/workflows/release.yml`](../.github/workflows/release.yml). The
`binaries` job builds one binary for each of four targets: Linux x86_64, Linux
arm64, macOS arm64 and Windows x86_64. The job then tests each binary. The test
runs `--version`, renders an example, and renders a document that imports a
bundled package. The `github-release` job attaches the binaries to the GitHub
Release.
