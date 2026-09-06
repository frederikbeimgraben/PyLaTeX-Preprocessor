# Changelog

This file lists each notable change to PyTeX. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-09-06

### Added
- **TeX math in a Markdown document.** `$…$` sets a formula in the line and a
  paragraph `$$…$$` sets one on its own line, the syntax that KaTeX and pandoc
  use. The body reaches LaTeX unescaped, and each formula loads amsmath and
  amsfonts. A price such as "$5 und $6" stays prose: the opening `$` takes no
  space behind it, the closing `$` no space in front of it and no digit behind
  it. A `\$` stays a dollar sign. The converter rebuilds the Markdown source of
  the inline nodes first, so an escape inside a formula (`\,`) keeps its
  backslash.

## [1.1.0] - 2026-08-06

### Added
- **A caller can now name the logos of a document instead of picking a
  corporate-design variant.** `HSRTReport` takes a `footer_logos` tuple next
  to the `logos` tuple it already had. `None` keeps the logo set of the
  variant, so nothing changes for a document that gives no list.
  `build_protocol` passes both lists through, and the Markdown frontmatter and
  the `--config` JSON read them from the keys `logos`/`logo` and
  `footer_logos`/`footer_logo`. An explicit footer set also turns the footer
  on, so the key never names a logo that no page shows.
- **The `protocol` variant**, a meeting protocol with no corporate design of
  its own. A platform that defines its own designs at run time uses this
  variant and names the logos, instead of one variant name for each design.

### Fixed
- **An uploaded logo now reaches the document build through the API.**
  `render_blob` writes the request assets into the work directory *before* the
  render step, and no longer only before the compile step. The render step
  then maps each entry of the `logos` and `footer_logos` config keys that
  names an asset to the absolute path of that asset. Before, the document
  build resolved such a name against the working directory of the process,
  which is not the work directory, and the build failed with "unknown logo".
  The asset-name check is unchanged: an asset must still be a plain file name
  with no path separator, and it must not carry the name of the rendered
  `.tex` file.

## [1.0.6] - 2026-06-10

### Fixed
- **The biber download now checks that the binary runs, and falls back.** The
  candidate list for Linux x86_64 offers the *musl* build first. That build
  links dynamically against the musl loader. A glibc-only host, for example
  Debian slim, cannot exec it at all (`No such file or directory`). The
  tectonic binary then stopped with "Running external tool biber … No such
  file or directory", although biber was on PATH. `_ensure_biber` now runs
  each downloaded candidate. When a candidate does not run, PyTeX falls back
  to the next one, the glibc build.

## [1.0.5] - 2026-06-10

### Fixed
- **A biblatex document now compiles through the API without a pre-installed
  biber.** The preamble of a report and of a meeting protocol always loads
  `biblatex`, so the tectonic binary calls `biber`. The compile path of the
  API never provided biber, unlike `run_tectonic` in the builder. A container
  with only the tectonic binary then failed with `Running external tool biber
  … No such file or directory`. The API compile now reads the BCF file and
  puts a version-matched biber on the PATH of the child process. PyTeX
  downloads that biber and caches it. This runs only when the document uses
  biblatex. A plain document skips the extra compile pass.

## [1.0.3] - 2026-06-10

### Fixed
- **PyTeX writes the logos to disk as a best-effort step, and a render without
  a converter no longer fails.** Version 1.0.2 made the Markdown render path
  write the logos to disk. `inkscape` converts an SVG logo. A render on a host
  without `inkscape` on PATH then failed. The sandbox warm-up, which
  renders every variant, is one such render. The step now logs a missing
  converter or a conversion error and continues. So a report or meeting
  protocol with a PDF logo builds. A variant with an SVG logo renders without
  that logo instead of a stopped render.

## [1.0.2] - 2026-06-10

### Fixed
- **A Markdown report build and a Markdown meeting protocol build now write
  their logos and inline images to disk.** The tikz title overlay and footer
  overlay name each logo by the relative path `logos/<file>`. The Markdown
  render path wrote only the inline fonts into the temporary work directory.
  The tectonic binary then failed with `Unable to load picture or PDF file
  'logos/...'`. `_render_markdown_source` now also calls `write_inline_logos`
  and `write_inline_images` on the document when the document has them. This
  mirrors the render path of the builder and of Python input. A plain document
  is unaffected.

## [1.0.1] - 2026-06-09

### Fixed
- **A Markdown report build and a Markdown meeting protocol build now write
  their bundled fonts to disk.** The report variants and meeting protocol
  variants (`report`, `report-makers`, `protocol-asta`, `protocol-stupa`) load
  the bundled DIN and Blender fonts with the fontspec option `Path=fonts/...`.
  The Markdown render path never wrote those TTF files into the temporary work
  directory. XeTeX then failed with `Package fontspec Error: The font
  "Blender-Medium" cannot be found`. `_render_markdown_source` now gets the
  temporary work directory and writes the inline fonts of the document into it.
  This mirrors the render path of Python input. A plain document is unaffected.

## [1.0.0] - 2026-06-04

The first stable release. PyTeX now freezes the public API under Semantic
Versioning. The **Stability** section in the README states what the freeze
covers. The main addition is a render API for input you do not trust. The two
breaking changes are factory renames.

### BREAKING
- **PyTeX renamed the font-size switch factories to the exact LaTeX spelling.**
  The old PascalCase names could not all exist together, because `\large`,
  `\Large` and `\LARGE` collide in case-insensitive PascalCase. That collision
  forced the names `LargeMid`, `LargeBig` and `HugeBig`. Each factory now
  matches its LaTeX command exactly. The registry keys, which you use in an
  inline `pytex(...)` marker, match it too:

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

  The meaning of two names changed. The old `Large` and `Huge` rendered
  `\large` and `\huge`. The new `Large` and `Huge` render `\Large` and `\Huge`.
  PyTeX gives no alias for the old names. An alias on the reused `Large` and
  `Huge` names would change the output without a warning, so the break is
  clean. The font family, series and shape switches are unchanged.
- **PyTeX renamed the `\fill` length factory from `Fill` to `Fill_len`.** The
  length (`pytex.commands.lengths.Fill`) and the TikZ `\fill` path command
  (`pytex_tikz.Fill`) both used the registry key `"Fill"`. So a reverse lookup
  and the `pytex(...)` namespace resolved to the one that imported last. The
  length now carries the `_len` suffix, as `Arraystretch_len` already does.
  That leaves the bare `Fill` key to TikZ. The deprecated
  `pytex.commands.lengths.Fill` alias still imports and raises a
  `DeprecationWarning`. A future major release can remove it.

### Added
- **`pytex_api`, a library that takes bytes and returns bytes.** It takes the
  source bytes of a Markdown, `.tex` or `.tex.py` input file. It returns the
  rendered `.tex` file or the compiled PDF as bytes. The caller never touches
  the file system, because all input and output stays in a temporary work
  directory per request. PyTeX removes that directory on return. The trust
  level gates code execution. `untrusted` is the default. A build at
  `untrusted` or `sandboxed` refuses Python execution and makes the
  code-execution surfaces of a `.tex` or Markdown input inert. It also forces
  shell-escape off, blocks the network during the request, and applies limits
  on CPU time, memory and file size plus a package allowlist. A build at
  `trusted` unlocks the full pipeline. Malformed or hostile input becomes a
  typed error, for example a `CompileError`. The caller sees no file path and
  no stack trace. Two async renders stay isolated from each other.
- **The rootless Podman sandbox** for a compile at `untrusted` or `sandboxed`.
  The sandbox uses `--network none`, a read-only root file system,
  `--cap-drop ALL`, no-new-privileges, the default seccomp profile, and cgroup
  caps on memory, pids and CPU. If Podman is not available, such a compile
  fails closed and reports why. PyTeX never falls back to the weaker
  in-process `setrlimit` and timeout floor for input it does not trust.
- **The `pytex-sandbox-init` console script.** It checks that Podman is
  present and that the rootless subuid and subgid ranges exist. It then builds
  the sandbox image and warms the bundle cache. It also turns a raw Podman
  error into a hint that tells you what to do.
- **Trust gating in the command (`--untrusted` and `--trust-level`).** The
  `pytex` command keeps the trust level `trusted` by default. It runs a `.py`
  input file. It evaluates an inline `pytex(...)` marker in a `.tex` file and
  a Markdown `eval` comment. It also turns shell-escape on. Use the default
  only for your own documents. `--untrusted` is the short form of
  `--trust-level untrusted`. `--untrusted` and `--trust-level sandboxed` route
  the build through the trust policy of `pytex_api` instead. The default is
  unchanged, so an existing command line behaves as before.
- **Font-independent Unicode in Markdown prose.** The tectonic binary compiles
  with XeTeX, and XeTeX does no font fallback. A code point that the DIN text
  font lacks then prints as a blank "tofu" box. A table now rewrites such a
  character. It maps `€` to `\euro{}`, and it maps `→ ↔ ≤ ≥ ·` to inline math
  (`\rightarrow \leftrightarrow \leq \geq \cdot`). A character that the table
  does not map, and that is not in every bundled DIN weight, becomes a
  `\texttt{[missing glyph]}` placeholder. PyTeX also raises a
  `MissingGlyphWarning` that names the character and its `U+XXXX` code point.
  So silent tofu never reaches the PDF. PyTeX reads the DIN coverage from the
  `cmap` tables of the bundled fonts, which needs no new dependency. A code
  span and a code block stay verbatim.
- **Custom report logos.** A report can set its own logo with the `logo` or
  `logos` frontmatter key. The value can mix a vendored logo name and a file
  path (`logos: [INF, /path/to/brand.svg]`).
- **Golden-file regression tests** (`tests/golden/`) freeze the rendered
  LaTeX. There is one sample per Markdown variant (`plain`, `report`,
  `protocol-asta`, `protocol-stupa`), plus one `.tex.py` node tree. The test
  renders each sample to a string and runs no compile pass. It then compares
  the string byte for byte against the golden file in the repository. So a
  refactor cannot change the output without a test failure. To write the
  golden files again, run `PYTEX_UPDATE_GOLDEN=1 pytest tests/golden`.
- **PyTeX freezes the 1.0 public API.** Every package declares an explicit
  `__all__`. The README has a new **Stability** section. It states what
  Semantic Versioning covers: the exported names plus the registry keys that
  an inline `pytex(...)` marker can reach. It also states what is internal: a
  name with a leading underscore, a module with a leading underscore, and
  anything outside `__all__`.
- **A standalone binary for Linux arm64** in each release, next to the
  binaries for x86_64, macOS and Windows.

### Changed
- **PyTeX added `eurosym` to the package allowlist** for `untrusted` and
  `sandboxed`. A `€` in Markdown from a source you do not trust now renders
  instead of a `TrustError`.
- **PyTeX moved the general components into a new `pytex_components`
  package.** The package holds the colored boxes, the voting tally, the draft
  watermark, and the word-count macros. It also holds the conditional and
  smart page breaks, the author-year `Fcite`, and the cleveref labels. They
  carry no HSRT branding and need only the `pytex` core package.
  `pytex_hsrtreport` re-exports them, so an existing import keeps working. The
  behavior is unchanged.
- **Hardened setup.** The cache for the tectonic binary and for biber moved out
  of `/tmp` to `$XDG_CACHE_HOME/pytex`, or to `~/.cache/pytex`, so the cache
  survives a reboot. There is a fallback for an unset `HOME`. The sandbox image
  matches the host architecture, x86_64 or aarch64. The cache warm-up runs a
  real compile per variant. A failed download, and a t-string error on a Python
  older than 3.14, now give a message that tells you what to do.

### Fixed
- **Box nesting is now safe under concurrency.** `_render_depth` moved to a
  `ContextVar`. Two concurrent async renders no longer corrupt the box-nesting
  depth and the opacities of each other.
- **The report footer on a back-matter page.** The line "Seite N von M" was
  missing on every back-matter page. The bibliography, which is the last page
  of the document, shows this best. The line now renders. The footer of the
  front matter and of the main matter is unchanged.

## [0.4.7] - 2026-06-04

### Added
- Title-page headings that you can configure. The frontmatter keys
  `abstract_heading` and `keywords_heading`, and their aliases, replace the
  default labels "Abstract" and "Keywords".

### Fixed
- The cache for the SVG to PDF conversion now uses the file content as its
  key. An edited vendored logo, for example the left-aligned MAKERS title-page
  logo, converts again instead of a stale PDF.
- PyTeX now aligns the lines of a title that wraps. The optical kern for the
  first line left the later lines of a two-line title offset from the first
  line. That kern is gone.

## [0.4.6] - 2026-06-04

### Added
- **Markdown citations in the Pandoc syntax.** `[@key]` and `[@key, p. 5]`
  render as `\autocite`, `[@a; @b]` renders as `\autocite{a,b}`, and a
  narrative `@key` renders as `\textcite`. A key can hold punctuation inside,
  but not at the end, so a sentence period never becomes part of the key. The
  Markdown converter leaves a code span and an e-mail address alone. Each
  citation adds the `biblatex` package requirement.
- **A bibliography from the frontmatter.** The `bibliography:` key (also
  `literatur` and `bibliografie`) takes inline BibTeX as a `|` block scalar or
  the path of a `.bib` file. A report writes it with `filecontents` and
  `\addbibresource`, so the document stays self-contained. The report then
  renders `\printbibliography` with the numeric biblatex style.
- **YAML block scalars** in the frontmatter: `|` for literal and `>` for
  folded, both with chomping indicators. A value can now span several lines,
  for example an inline bibliography.
- **The `report-makers` variant** with the MAKERS logo. The logo sits on the
  left on the title page and on the right in the footer.
- **The `postnote` argument of `Autocite`** for the `\autocite[note]{key}`
  form.

### Changed
- **PyTeX merged `pytex_protocol` into `pytex_markdown`.** The general
  frontmatter parser moved to `pytex_markdown.frontmatter`. The meeting
  protocol rendering moved to `pytex_markdown.protocol`. `pytex_protocol` stays
  as a deprecated shim that re-exports the public API.
- A Markdown table now gets vertical space (`\addvspace`) above and below.
- The biber downloader now covers every upstream platform: Linux x86_64 with
  glibc and with musl, Linux aarch64, macOS x86_64 and universal, and Windows.
  On Linux x86_64 it prefers the static musl build. That fixes the
  `libnsl.so.1` load failure.

## [0.4.5] - 2026-06-03

### Added
- The MAKERS logos and a first `report-makers` variant.

## [0.4.4] - 2026-06-03

### Fixed
- The Markdown converter renders the euro sign `€` with `\euro{}` from
  `eurosym`, which is safe under the DIN font. It also escapes a literal `"`
  for babel.

## [0.4.3] - 2026-06-02

### Fixed
- PyTeX resolves a Markdown image path to an absolute path. PyTeX also fixes
  the data lines on the report title page.

## [0.4.2] - 2026-06-02

### Added
- Markdown tables, wrapping for code and tables, smart links, and math arrows.

### Changed
- The project uses the GPL-3.0-or-later license.

## [0.4.1] - 2026-06-02

### Added
- Examples for the PEP 750 template strings `tex(t"...")`. An `HSRTReport`
  built again with t-strings.

### Fixed
- PyTeX strips the outer whitespace inside a math delimiter.

## [0.4.0] - 2026-06-02

### Added
- A standalone PyInstaller binary with a bundle config.
- The template strings `tex(t"...")` (PEP 750, Python 3.14 or later).

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
