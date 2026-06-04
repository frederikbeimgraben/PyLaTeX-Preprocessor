# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - Unreleased

### Changed
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
