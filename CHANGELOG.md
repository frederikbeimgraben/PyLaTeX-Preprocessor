# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - Unreleased

### Added
- **Font-independent Unicode handling in Markdown prose.** tectonic (XeTeX) does
  no font fallback, so a code point the DIN text font lacks would render as a
  blank "tofu" box. A data-driven table now rewrites such characters to
  font-independent constructs: `€` → eurosym `\euro{}`, and `→ ↔ ≤ ≥ ·` →
  inline-math `\rightarrow \leftrightarrow \leq \geq \cdot` (the arrow targets
  match the existing ASCII-arrow rewrites; `·` maps to the math `\cdot`, not the
  font-dependent `\textperiodcentered`). The `€` fix is now the first table entry
  rather than a special case; code spans/blocks are left verbatim.
- A character that is neither mapped nor present in every bundled DIN weight is
  genuinely unrenderable: it becomes a `\texttt{[missing glyph]}` placeholder and
  raises a `MissingGlyphWarning` (naming the char and its `U+XXXX` code point),
  so silent tofu never reaches the PDF. DIN coverage comes from parsing the
  bundled fonts' `cmap` tables directly (no new dependency).

### Changed
- `eurosym` is now on the UNTRUSTED/SANDBOXED package allowlist, so a `€` in
  untrusted Markdown renders instead of being rejected with a `TrustError`.
- **BREAKING — font size switch factories renamed to the verbatim LaTeX
  spelling.** The `\large`/`\Large`/`\LARGE` and `\huge`/`\Huge` escalations
  cannot all fit strict PascalCase without colliding, which forced the awkward
  `LargeMid` / `LargeBig` / `HugeBig` "Big"-suffix names. Python identifiers are
  case-sensitive, so the factories (and their registry keys, exposed to inline
  `pytex(...)` markers) now mirror the LaTeX command exactly:

  | old             | new            | LaTeX command |
  | --------------- | -------------- | ------------- |
  | `Tiny`          | `tiny`         | `\tiny`       |
  | `Scriptsize`    | `scriptsize`   | `\scriptsize` |
  | `Footnotesize`  | `footnotesize` | `\footnotesize` |
  | `Small`         | `small`        | `\small`      |
  | `Normalsize`    | `normalsize`   | `\normalsize` |
  | `Large`         | `large`        | `\large`      |
  | `LargeMid`      | `Large`        | `\Large`      |
  | `LargeBig`      | `LARGE`        | `\LARGE`      |
  | `Huge`          | `huge`         | `\huge`       |
  | `HugeBig`       | `Huge`         | `\Huge`       |

  Note the semantic flip: the old `Large`/`Huge` emitted `\large`/`\huge`; they
  now emit `\Large`/`\Huge`. No deprecation aliases are provided — an alias for
  the reused `Large`/`Huge` names would silently change behaviour, so a clean
  break is safer pre-1.0. Font family/series/shape switches are unchanged.
- **BREAKING — the `\fill` length factory is renamed `Fill` -> `Fill_len`.**
  `pytex.commands.lengths.Fill` (the rubber length `\fill`) and `pytex_tikz.Fill`
  (the TikZ `\fill` path command) both registered under the single registry key
  `"Fill"`, so the reverse lookup and the `pytex(...)` eval namespace resolved to
  whichever module imported last. The length now uses the `_len` suffix already
  established by `Arraystretch_len` (which dodges the `Arraystretch` table
  command the same way), leaving the bare `Fill` key to the TikZ command. A
  deprecated `pytex.commands.lengths.Fill` alias keeps importing and emits a
  `DeprecationWarning`; it may be removed in a future major. The TikZ `Fill` is
  unchanged.

### Public API
- **1.0 API surface frozen.** Every package now declares an explicit, consistent
  `__all__`; the README gained a `Stability` section stating what is covered by
  Semantic Versioning (the names a package exports, plus the registry keys
  reachable from `pytex(...)` markers) and what is internal (leading-underscore
  names, underscore-prefixed modules such as `pytex_api._policy` /
  `pytex_api._compile`, and anything outside `__all__`).

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

[0.4.7]: https://github.com/frederikbeimgraben/PyTeX-Preprocessor/releases/tag/v0.4.7
[0.4.6]: https://github.com/frederikbeimgraben/PyTeX-Preprocessor/releases/tag/v0.4.6
[0.4.5]: https://github.com/frederikbeimgraben/PyTeX-Preprocessor/releases/tag/v0.4.5
[0.4.4]: https://github.com/frederikbeimgraben/PyTeX-Preprocessor/releases/tag/v0.4.4
[0.4.3]: https://github.com/frederikbeimgraben/PyTeX-Preprocessor/releases/tag/v0.4.3
[0.4.2]: https://github.com/frederikbeimgraben/PyTeX-Preprocessor/releases/tag/v0.4.2
[0.4.1]: https://github.com/frederikbeimgraben/PyTeX-Preprocessor/releases/tag/v0.4.1
[0.4.0]: https://github.com/frederikbeimgraben/PyTeX-Preprocessor/releases/tag/v0.4.0
