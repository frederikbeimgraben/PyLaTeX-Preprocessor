# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.4] - 2026-06-10

### Fixed
- **biblatex documents render via the API without a pre-installed biber.** The
  report/protocol preamble always loads `biblatex`, so tectonic shells out to
  `biber`; the API compile path (unlike the builder's `run_tectonic`) never set
  it up, so a container with only tectonic failed with `Running external tool
  biber … No such file or directory`. The API compile now probes the BCF and
  puts a version-matched biber on the child's PATH (download+cached), but only
  when the document actually uses biblatex — plain docs skip the extra pass.

## [1.0.3] - 2026-06-10

### Fixed
- **Logo materialisation is best-effort and no longer crashes converter-less
  renders.** 1.0.2 made the Markdown render path materialise logos, but SVG
  logos are converted via `inkscape`; a render without it on PATH (e.g. the
  sandbox warm-up that renders every variant) then failed hard. Logo/image
  materialisation now logs and continues on a missing converter / conversion
  error, so PDF-logo report/protocol builds work and SVG variants degrade
  gracefully instead of aborting the render.

## [1.0.2] - 2026-06-10

### Fixed
- **Markdown report/protocol builds now materialise their logos (and inline
  images).** The tikz title/footer overlays reference logos by the relative
  `logos/<file>` path, but the Markdown render path only wrote the inline fonts
  into the compile workdir — tectonic then failed with `Unable to load picture
  or PDF file 'logos/...'`. `_render_markdown_source` now also calls the
  document's `write_inline_logos`/`write_inline_images` when present (mirroring
  the builder/Python render path); plain documents are unaffected.

## [1.0.1] - 2026-06-09

### Fixed
- **Markdown report/protocol builds now materialise their bundled fonts.** The
  report/protocol variants (`report`, `report-makers`, `protocol-asta`,
  `protocol-stupa`) embed the bundled DIN/Blender fonts via fontspec's
  `Path=fonts/...`, but the Markdown render path never wrote those TTFs into the
  compile workdir — XeTeX then failed with `Package fontspec Error: The font
  "Blender-Medium" cannot be found`. `_render_markdown_source` now receives the
  workdir and writes the document's inline fonts into it (mirroring the Python
  render path); plain documents are unaffected.

## [1.0.0] - 2026-06-04

First stable release. The public API is now frozen under Semantic Versioning —
see the **Stability** section in the README for exactly what that covers. The
headline addition is a sandboxed render API for untrusted input; the breaking
changes are two factory renames.

### BREAKING
- **Font size switch factories renamed to the verbatim LaTeX spelling.** The old
  PascalCase names could not all coexist (`\large`/`\Large`/`\LARGE` collide in
  case-insensitive PascalCase), which forced the awkward `LargeMid` / `LargeBig`
  / `HugeBig`. The factories — and their registry keys, used in inline
  `pytex(...)` markers — now mirror the LaTeX command exactly:

  | old             | new            | LaTeX command   |
  | --------------- | -------------- | --------------- |
  | `Tiny`          | `tiny`         | `\tiny`         |
  | `Scriptsize`    | `scriptsize`   | `\scriptsize`   |
  | `Footnotesize`  | `footnotesize` | `\footnotesize` |
  | `Small`         | `small`        | `\small`        |
  | `Normalsize`    | `normalsize`   | `\normalsize`   |
  | `Large`         | `large`        | `\large`        |
  | `LargeMid`      | `Large`        | `\Large`        |
  | `LargeBig`      | `LARGE`        | `\LARGE`        |
  | `Huge`          | `huge`         | `\huge`         |
  | `HugeBig`       | `Huge`         | `\Huge`         |

  Note the semantic flip: the old `Large`/`Huge` emitted `\large`/`\huge`; they
  now emit `\Large`/`\Huge`. No aliases are provided — an alias on the reused
  `Large`/`Huge` names would silently change behaviour, so the break is clean.
  Font family/series/shape switches are unchanged.
- **`\fill` length factory renamed `Fill` → `Fill_len`.** The length
  (`pytex.commands.lengths.Fill`) and the TikZ `\fill` path command
  (`pytex_tikz.Fill`) both registered under the key `"Fill"`, so reverse lookup
  and the `pytex(...)` namespace resolved to whichever imported last. The length
  now takes the `_len` suffix (as `Arraystretch_len` already does), leaving the
  bare `Fill` key to TikZ. A deprecated `pytex.commands.lengths.Fill` alias still
  imports and emits a `DeprecationWarning`; it may be removed in a future major.

### Added
- **`pytex_api` — blob-in, blob-out render library.** Takes source bytes
  (Markdown, `.tex`, or `.tex.py`) and returns rendered `.tex` or compiled PDF
  bytes; the caller never touches the filesystem (all I/O runs in a per-request
  temp dir that is removed on return). Trust levels gate code execution:
  `UNTRUSTED` (default) and `SANDBOXED` refuse Python exec, render
  `.tex`/Markdown code surfaces inert, force shell-escape off, block in-request
  network, apply CPU/memory/file-size limits and a package allowlist; `TRUSTED`
  unlocks the full pipeline. Malformed or hostile input maps to a typed
  `CompileError` with no path or stacktrace leaked to the caller. Async renders
  are isolated from each other.
- **Rootless Podman sandbox** for untrusted/sandboxed compiles: `--network
  none`, read-only rootfs, `--cap-drop ALL`, no-new-privileges, the default
  seccomp profile, and cgroup memory/pids/cpu caps. Falls back to the in-process
  `setrlimit` + timeout floor (with a warning, never silently) when Podman is
  unavailable.
- **`pytex-sandbox-init` console script** — preflight (podman present? rootless
  subuid/subgid?), build the sandbox image, warm the bundle cache, and turn raw
  podman errors into actionable hints.
- **CLI trust gating (`--untrusted` / `--trust-level`).** The `pytex` CLI stays
  a **trusted** context by default: it executes `.py` inputs, evaluates `.tex`
  `pytex(...)` replacements and Markdown `eval` comments, and enables
  shell-escape — safe only for your own documents. `--untrusted` (shorthand for
  `--trust-level untrusted`) or `--trust-level sandboxed` route the build through
  the `pytex_api` trust policy instead. The default is unchanged, so existing
  invocations behave as before.
- **Font-independent Unicode in Markdown prose.** tectonic (XeTeX) does no font
  fallback, so a code point the DIN text font lacks renders as a blank "tofu"
  box. A data-driven table rewrites such characters: `€` → `\euro{}`, and
  `→ ↔ ≤ ≥ ·` → inline math (`\rightarrow \leftrightarrow \leq \geq \cdot`). A
  character that is neither mapped nor present in every bundled DIN weight
  becomes a `\texttt{[missing glyph]}` placeholder and raises a
  `MissingGlyphWarning` naming the character and its `U+XXXX` code point, so
  silent tofu never reaches the PDF. DIN coverage is read from the bundled fonts'
  `cmap` tables (no new dependency); code spans and blocks are left verbatim.
- **Custom report logos.** A report can set its own logo via the `logo`/`logos`
  frontmatter key, mixing vendored names and file paths
  (`logos: [INF, /path/to/brand.svg]`).
- **Golden-file regression tests** (`tests/golden/`) freeze the `.tex` render
  output — one sample per Markdown variant (`plain`, `report`, `protocol-asta`,
  `protocol-stupa`) plus a `.tex.py` node tree — rendered to a string (no
  tectonic/PDF) and compared byte-for-byte against checked-in goldens, so a
  refactor cannot silently change the output. Regenerate with
  `PYTEX_UPDATE_GOLDEN=1 pytest tests/golden`.
- **1.0 public API frozen.** Every package declares an explicit `__all__`; the
  README gained a **Stability** section stating what SemVer covers (exported
  names plus the registry keys reachable from `pytex(...)`) and what is internal
  (leading-underscore names, underscore-prefixed modules, anything outside
  `__all__`).
- **Linux arm64 standalone binary** in releases, alongside x86_64, macOS and
  Windows.

### Changed
- **`eurosym` added to the untrusted/sandboxed package allowlist**, so a `€` in
  untrusted Markdown renders instead of failing with a `TrustError`.
- **Generic widgets extracted into a new `pytex_components` package** — callout
  boxes, voting tally, draft watermark, word-count macros, conditional/smart page
  breaks, the author-year `Fcite`, and cleveref labels. They carry no HSRT
  branding and depend only on core pytex; `pytex_hsrtreport` re-exports them, so
  existing imports keep working. No behaviour change.
- **Setup hardening.** The tectonic/biber binary cache moved out of `/tmp` to
  `$XDG_CACHE_HOME/pytex` (or `~/.cache/pytex`) so it survives a reboot, with a
  HOME-unset fallback. The sandbox image is arch-aware (x86_64 / aarch64), the
  cache warm-up runs a real compile per variant, and failed-download /
  Python-3.14 t-string errors now give actionable messages.

### Fixed
- **Concurrency-safe box nesting.** `_render_depth` moved to a `ContextVar`, so
  concurrent async renders no longer corrupt each other's box-nesting depth and
  opacities.
- **Report footer on back-matter pages.** "Seite N von N" was missing on every
  back-matter page — most visibly the bibliography, the document's last page — and
  now renders correctly. Front- and main-matter footers are unchanged.

## [0.4.7] - 2026-06-04

### Added
- Configurable title-page headings: `abstract_heading` / `keywords_heading`
  frontmatter keys (with aliases) override the default "Abstract" / "Keywords"
  labels.

### Fixed
- Content-address the SVG→PDF cache so an edited vendored logo (e.g. the
  left-aligned MAKERS title-page logo) reconverts instead of reusing a stale PDF.
- Align wrapped title-page titles: the per-first-line optical kern that left a
  two-line title's later lines offset from the first is gone.

## [0.4.6] - 2026-06-04

### Added
- **Markdown citations (Pandoc syntax).** `[@key]` and `[@key, p. 5]` render as
  `\autocite`, `[@a; @b]` as `\autocite{a,b}`, and a narrative `@key` as
  `\textcite`. Keys may contain internal punctuation but not trailing, so a
  sentence period is never swallowed; code spans and e-mail addresses are left
  alone. Each citation registers the `biblatex` requirement automatically.
- **Bibliographies from frontmatter.** A `bibliography:` key (also `literatur` /
  `bibliografie`) accepts either inline BibTeX as a `|` block scalar or a path to
  a `.bib` file. Reports embed it via `filecontents` + `\addbibresource` (so the
  document stays self-contained) and emit `\printbibliography` with the numeric
  biblatex style.
- **YAML block scalars** (`|` literal and `>` folded, with chomping indicators)
  in frontmatter, enabling multi-line values such as an inline bibliography.
- **`report-makers` variant** branded with the MAKERS logo — left-aligned on the
  title page, right-aligned in the footer.
- **`Autocite` postnote** argument for the `\autocite[note]{key}` form.

### Changed
- **Merged `pytex_protocol` into `pytex_markdown`.** The generic frontmatter
  parser moved to `pytex_markdown.frontmatter` and the meeting-protocol rendering
  to `pytex_markdown.protocol`. `pytex_protocol` remains as a deprecation shim
  re-exporting the public API.
- Markdown tables now get vertical breathing room (`\addvspace`) above and below.
- The biber auto-downloader mirrors every upstream platform (glibc/musl Linux
  x86_64, Linux aarch64, macOS x86_64/universal, Windows) and prefers the static
  musl build on Linux x86_64, fixing the `libnsl.so.1` load failure.

## [0.4.5] - 2026-06-03

### Added
- MAKERS logos and an initial `report-makers` variant.

## [0.4.4] - 2026-06-03

### Fixed
- Render the Euro sign `€` via `eurosym`'s `\euro{}` (DIN-font safe) and escape a
  literal `"` for babel.

## [0.4.3] - 2026-06-02

### Fixed
- Resolve Markdown image paths absolutely; report title-page data lines.

## [0.4.2] - 2026-06-02

### Added
- Markdown tables, code/table wrapping, smart links and math arrows.

### Changed
- Licensed under GPL-3.0-or-later.

## [0.4.1] - 2026-06-02

### Added
- `tex(t"...")` PEP 750 template-string examples; an HSRTReport rebuilt with
  t-strings.

### Fixed
- Strip outer whitespace inside math delimiters.

## [0.4.0] - 2026-06-02

### Added
- Standalone PyInstaller binary with a bundle config.
- `tex(t"...")` template strings (PEP 750, Python 3.14+).

[Unreleased]: https://github.com/frederikbeimgraben/PyTeX-Preprocessor/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/frederikbeimgraben/PyTeX-Preprocessor/releases/tag/v1.0.0
[0.4.7]: https://github.com/frederikbeimgraben/PyTeX-Preprocessor/releases/tag/v0.4.7
[0.4.6]: https://github.com/frederikbeimgraben/PyTeX-Preprocessor/releases/tag/v0.4.6
[0.4.5]: https://github.com/frederikbeimgraben/PyTeX-Preprocessor/releases/tag/v0.4.5
[0.4.4]: https://github.com/frederikbeimgraben/PyTeX-Preprocessor/releases/tag/v0.4.4
[0.4.3]: https://github.com/frederikbeimgraben/PyTeX-Preprocessor/releases/tag/v0.4.3
[0.4.2]: https://github.com/frederikbeimgraben/PyTeX-Preprocessor/releases/tag/v0.4.2
[0.4.1]: https://github.com/frederikbeimgraben/PyTeX-Preprocessor/releases/tag/v0.4.1
[0.4.0]: https://github.com/frederikbeimgraben/PyTeX-Preprocessor/releases/tag/v0.4.0
