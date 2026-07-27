# Bug backlog

This document lists the defects that the documentation rewrite found. Nobody
fixed them. The rewrite changed prose only.

Every entry names a file, a line and a failure scenario. The line number points
at the code as it stands after the rewrite. A rewrite moves no code, so the
number also matches the commit before the rewrite.

The agents that read the code reported these defects. Treat each one as a
report, not as a proven fault. Confirm the scenario before you write a fix.

| Severity | Count |
| --- | --- |
| high | 36 |
| medium | 129 |
| low | 105 |
| **total** | **270** |

## Severity high

### `examples/mixed.tex.py:18` — The example imports a submodule that no longer exists, so `pytex examples/mixed.tex.py` fails at import

Line 18 is `from pytex_hsrtreport.boxes import SuccessBox`. The boxes module moved to `pytex_components`; there is no `src/pytex_hsrtreport/boxes.py` any more. `pytex_hsrtreport/__init__.py` does `from pytex_components import (..., boxes, ...)`, which binds `boxes` as an attribute of the package but never registers `pytex_hsrtreport.boxes` in sys.modules, and `from a.b import c` requires `a.b` to be importable as a module. Verified by running the real builder: `main(['examples/mixed.tex.py'])` prints `==> Rendering mixed.tex.py` then `error: error while importing mixed.tex.py: No module named 'pytex_hsrtreport.boxes'`, exit 1. Both the render and the `--build` path fail, from any working directory. `import pytex_hsrtreport; pytex_hsrtreport.boxes.SuccessBox` still resolves, which is why the move looked safe. Consequence: the documented example of mixing the Python API with Markdown cannot run, and the previously reported IncludeMarkdown working-directory defect is unreachable because the file never finishes importing.

### `src/pytex/commands/builtin.py:385` — _is_item misses Item() nodes that have a body, so Itemize emits a double \item

Item(body) returns a Concat, not a ControlSequence, whenever body is not None. _is_item only returns True for a bare ControlSequence named "item". So Itemize(Item("a"), Item("b")) wraps each already-built item a second time. Verified render: \begin{itemize}\item \item a\item \item b\end{itemize}. LaTeX typesets an extra empty bullet before every entry. The same path affects Enumerate. The _is_item guard only works for Item() called with no body, which is the rare case.

### `src/pytex/commands/builtin.py:545` — Verb does not check that delim is absent from body, and delim="*" silently selects \verb*

`Verb` interpolates `delim` and `body` with no validation. Verified: `Verb('a|b').rendered` is `\verb|a|b|`. LaTeX closes the verbatim group at the second `|`, typesets `a` verbatim, then typesets `b` in the normal font, then leaves a stray `|`. The caller gets silently wrong output with no error. Worse, `Verb('x', delim='*').rendered` is `\verb*x*`: LaTeX reads the `*` as the star form of `\verb` and takes `x` as the delimiter, so the body prints nothing and `\verb*` swallows document text until the next literal `x`. A newline in `body` gives a third failure, "LaTeX Error: \verb ended by end of line". A one-line guard that rejects a `body` containing `delim` (and rejects `delim in {'*', ' '}`) would turn all three into a clear Python error.

### `src/pytex/commands/captions.py:40` — Captionof never requires the caption package

`\captionof` is defined by the `caption` package (and by capt-of / float), not by the LaTeX kernel. The factory carries no @with_package, even though CAPTION is already imported on line 6 and used for Captionsetup on line 46. A .tex.py file whose only caption use is `Captionof("figure", Text("..."))` renders a preamble with no `\usepackage{caption}`, so the compile pass stops with "Undefined control sequence \captionof". tests/pytex/commands/test_new_modules.py:291 asserts only the rendered string, so it passes.

### `src/pytex/commands/definitions.py:146` — Def renders its body node into a string, so every package requirement of the body is lost

`Def` builds `Raw(f"\\def\\{cs}{{{body}}}")`. The f-string calls `TeX.__str__`, which returns `.rendered`, so the body node is flattened to text at construction time and never becomes a child node. `Raw` has no `requires`, so the requirement travels nowhere. Verified: `Euro().requires` is `frozenset({Package('eurosym')})`, but `Def('mycmd', Euro()).rendered` is `\def\mycmd{\euro{}}` and `Def('mycmd', Euro()).requires` is `None`. The preamble gets no `\usepackage{eurosym}` and the compile pass fails with "Undefined control sequence \euro". Every other factory in this group that takes a `TeX | str` body keeps it as a child of a `ControlSequence` or a `Concat`, so requirements propagate. `Def` is the only one that stringifies. The same flattening also drops the body from the node tree, so the optimize pass and the analysis pass cannot see labels or refs defined inside a `Def` body.

### `src/pytex/commands/definitions.py:157` — Def takes the control sequence name without a backslash while every other factory in the file takes it with one

`_cmd` renders the name straight into the braces via `Parameter(Raw(cs))`, so `Newcommand("\\foo", "x")` (Python source; the string is `\foo`) correctly gives `\newcommand{\foo}{x}`. `Def` supplies its own backslash in `Raw(f"\\def\\{cs}...")`, so it needs the bare name. A caller who follows the file's own convention and writes `Def("\\foo", "x")` gets `\def\\foo{x}`. In LaTeX `\\` is a line break, so the compile pass inserts a stray line break and then typesets the literal text `foo{x}` into the document. There is no error and no warning. Verified by rendering. The freshly rewritten docstring routes readers between the two factories, which makes the swap more likely.

### `src/pytex/commands/floats.py:136` — Multicols and Columnbreak never require the multicol package

Both factories build `multicols` / `\columnbreak` with no @with_package, and `multicol` is not defined in src/pytex/packages.py at all. A `.tex.py` file that does `__pytex__ = Multicols(2, body)` renders a document whose preamble has no `\usepackage{multicol}`, so the compile pass fails with "Environment multicols undefined". src/pytex_components/voting.py:18-22 already works around this by defining its own MULTICOL package, which confirms the gap for every other caller.

### `src/pytex/commands/listings.py:96` — Lstlisting emits the code on the \begin line, so listings swallows the rest of the document

Environment() builds Concat(Begin, body, End) with no separator, so Lstlisting("print(1)") renders the single line `\begin{lstlisting}print(1)\end{lstlisting}`. listings reads verbatim line by line: it drops everything after `\begin{lstlisting}` on that line ("Text dropped after begin of listing") and then scans following lines for `\end{lstlisting}` at line start. There is none, so it consumes the remainder of the rendered .tex file and the compile pass dies with a runaway-argument / file-ended error. The only in-repo caller works around this by hand: src/pytex_markdown/convert.py:386 passes `f"\n{code}\n"` with the comment "lstlisting reads the code from the line after". Any .tex.py file calling Lstlisting directly hits the bug. tests/pytex/commands/test_new_modules.py:284 only asserts the rendered substring, so it passes.

### `src/pytex/commands/tables.py:90` — Cmidrule passes trim as a bracket argument, which booktabs reads as rule thickness

booktabs spells the trim spec in parentheses: \cmidrule(lr){2-3}. The optional bracket argument is the rule thickness. Cmidrule("2-3", trim="lr") renders \cmidrule[lr]{2-3}, so booktabs tries to read "lr" as a dimension and the compile pass fails with "Illegal unit of measure (pt inserted)". Any use of the trim argument breaks the build.

### `src/pytex/commands/tables.py:105` — Arraystretch renders \arraystretch{factor}, which prints the factor as text

\arraystretch is not a command that takes an argument. It is a macro holding a number that you redefine, normally with \renewcommand{\arraystretch}{1.5}. Arraystretch("1.5") renders \arraystretch{1.5}, which expands \arraystretch to its current value and then typesets the literal text 1.5 into the document. Row spacing is unchanged and stray digits appear in the table. Compare Renewcommand in definitions.py, which is the correct route.

### `src/pytex/helpers/parenting.py:22` — attach() writes `_parent` onto the shared `Empty` singleton, so a process-global node gets a per-document parent

`Empty` is a module-level singleton (`Empty = EmptyTeX()` in model/empty.py) whose `_parent` is a class attribute set to None. `attach` calls `object.__setattr__(child, "_parent", parent)` unconditionally, which succeeds on `EmptyTeX` and creates an instance attribute on that one shared object. `Document.__post_init__` runs `attach(self, self.body, self.preamble)` and `preamble` defaults to `Empty`, so every `Document(...)` built without a preamble re-points the global. Verified: after `d1 = Document(body='a'); d2 = Document(body='b')`, `Empty.parent is d2` is True, and after the first call `Empty.__dict__` was `{'_parent': <Document body='a'>}`. `ControlSequence.__post_init__` does the same for any `Empty` in `params` (the `Parameters` type explicitly allows `EmptyTeX`), and `_coerce` in template.py returns `Empty` for a None interpolation. Failure: build document A, then document B, then ask an `Empty`-valued preamble or parameter for `.parents` — it returns document B's chain, so a pass that resolves a node's root through `parent` (analysis, optimize) attributes the node to the wrong document, and the answer depends on process-wide construction order instead of on the tree.

### `src/pytex/helpers/with_package.py:24` — coerce_package makes a new Package instead of reusing the registered one

coerce_package("cleveref") calls Package("cleveref") directly, bypassing DefinePackage and the module-level PACKAGES table, so the new instance has an empty `after` set and empty `options`. Package defines no __eq__/__hash__, so the fresh instance is not equal to packages.CLEVEREF and both survive into Document.packages. Document.ordered_packages() then dedups by name: `state[pkg.name]` is set by whichever duplicate `sorted(packages, key=name)` yields first, and since sort is stable that is frozenset iteration order, which depends on id-based hashes and varies per process. When the optionless duplicate wins, the preamble renders `\usepackage{cleveref}` with no `after={HYPERREF, AMSMATH}` constraint, so cleveref can be emitted before hyperref and tectonic aborts with cleveref's "must be loaded after hyperref" error. The same path drops `framemethod=tikz` for @with_package("mdframed"), which silently breaks mdframed rounded backgrounds. The failure is nondeterministic across runs of the same document.

### `src/pytex/model/color.py:137` — tint() and mix() drop the `spec`, so the base color never gets a `\definecolor`

`Color.hex("FF0000")` produces name `cFF0000` with a `spec`. Calling `.tint(20)` returns `Color(name="cFF0000!20", spec=None)`. Only the tint node ends up in the node tree, and `collect_colors` skips it because `spec is None`. The base node `cFF0000` is not in the tree at all, so no `\definecolor{cFF0000}{HTML}{FF0000}` line is ever rendered. LaTeX then fails with "Undefined color `cFF0000'". The same applies to `mix` and to `__or__`.

### `src/pytex/model/document.py:60` — Package `after` requirements are expanded one level only, so transitive packages are dropped

`Document.packages` builds the set with `for after in pkg.after | {pkg}` over the requirements found in the node tree. That comprehension is not recursive over `after`. Given CLEVEREF.after == {HYPERREF} and HYPERREF.after == {GRAPHICX}, a document whose only node requires CLEVEREF yields {CLEVEREF, HYPERREF} and never GRAPHICX. The rendered `.tex` therefore omits `\usepackage{graphicx}` and the compile pass fails with an undefined control sequence, even though the package graph named the requirement.

### `src/pytex/model/package.py:84` — Package.__post_init__ never runs, so PACKAGES misses directly built packages

`Package` is a plain class with a hand-written `__init__`; it is not a dataclass, and `__init__` never calls `__post_init__`. The registration into the module-level `PACKAGES` dict and the "Multiple Instances ... in circulation!" warning are therefore dead code. Concretely: `pytex.helpers.with_package.coerce_package("tikz")` calls `Package("tikz")` directly, so `PACKAGES["tikz"]` is never set. A later `DefinePackage("tikz", after={HYPERREF})` sees the name as absent, builds a second `Package` instance, and the two instances hash and compare as different objects. `Document.ordered_packages` then sorts by `name` and can render `\usepackage{tikz}` twice, or drop the ordering constraint that only one of the two instances carries.

### `src/pytex_analyze/optimize.py:199` — Optimize re-enables inline `pytex(...)` evaluation for a Raw that was explicitly marked allow_replacements=False

`_token_node` correctly honors `allow_replacements` in the `marker` branch (line 190), but the `dmath`, `imath` and `smath` branches rebuild the sub-content with a bare `Raw(dmath)` / `Raw(imath)` / `Raw(match.group("smath"))`. `Raw.allow_replacements` defaults to True, so `_optimize` recurses into a node whose replacement gate is now open. `_candidates` (lines 207 and 210) does the same for `\begin{x}..\end{x}` and `\cmd{..}` bodies. `Sanitize(untrusted, pytex=True)` and `pytex_api._render` (line 137, for a non-trusted trust level) both produce `Raw(..., allow_replacements=False)` exactly to keep untrusted markers inert, and `pytex_builder.build._optimize` (line 270) runs the optimize pass over the whole node tree. Verified: `Optimize(Raw(r'\[\iffalse{pytex(__import__("pathlib").Path("/tmp/pwned_optimize").write_text("x"))}\fi\]', allow_replacements=False))` created /tmp/pwned_optimize, while `.rendered` on the same node is inert. The guard then rejects the candidate so the rendered text is unchanged, which makes the code execution completely silent.

### `src/pytex_analyze/optimize.py:201` — The math branches drop `raw.namespace`, so Optimize raises NameError and aborts the build for a valid document

`_tokenize` builds `namespace = pytex_namespace(raw.namespace or {})` (line 166) and passes it to `_token_node`, but the `dmath`, `imath` and `smath` branches construct `Raw(dmath)` / `Raw(imath)` / `Raw(smath)` without the `namespace` argument. The recursive `_optimize` on that node therefore evaluates the marker against the registry plus builtins only. Verified: `Optimize(Raw(r'\[\iffalse{pytex(bump())}\fi\]', namespace={'bump': bump}))` raises `NameError: name 'bump' is not defined`, while `Raw(...).rendered` on the same node returns `\[7\]`. The exception is not caught anywhere in `_optimize`, so `pytex ... --build` on a document that puts a namespace-using marker inside display or inline math crashes with a traceback instead of building.

### `src/pytex_api/_compile.py:322` — A caller-supplied asset named document.tex overwrites the checked LaTeX and voids the package allowlist

compile_to_pdf writes the rendered LaTeX to workdir/"document.tex" at line 319, then writes every caller asset into the same directory at lines 322-323. validate_asset_name (_security.py:54) accepts "document.tex" as a perfectly ordinary plain file name. enforce_packages (_security.py:98) has already run against the rendered LaTeX, and nothing re-checks the file on disk. Concrete failure: render_blob(BuildRequest(source=b"ok", input_kind=InputKind.TEX, output_kind=OutputKind.PDF, trust=TrustLevel.UNTRUSTED, assets={"document.tex": b"\\documentclass{article}\\usepackage{shellesc}\\begin{document}x\\end{document}"})) passes the allowlist on the benign source, then compiles the attacker's replacement instead. The whole PACKAGE_ALLOWLIST / DANGEROUS_PACKAGES gate is bypassed for untrusted input. Only the Podman sandbox and the forced shell-escape-off remain. The same trick can overwrite build/ contents or, with tectonic_in_image=False, aim at other workdir names.

### `src/pytex_api/_compile.py:323` — An asset named document.tex overwrites the screened LaTeX after enforce_packages has run

compile_to_pdf writes `workdir/document.tex` from the rendered, allowlist-screened `latex` at line 319, then loops over `assets` at 322-323 and writes each one into the same directory. validate_asset_name accepts 'document.tex' (plain name, no separator), so BuildRequest(trust=SANDBOXED, output_kind=PDF, source=b'# hi', assets={'document.tex': b'\\documentclass{article}\\usepackage{pdftexcmds}...'}) replaces the screened file before tectonic ever opens it. Verified the overwrite ordering directly: after filter_assets + the same write loop, document.tex holds the attacker bytes. Result: enforce_packages, strip_markdown_eval_comments and the whole render-layer trust gate are bypassed - tectonic compiles caller LaTeX that was never screened, and the guarantee _render.py documents ('a forbidden \\usepackage fails whether the result is the rendered .tex file or the input to a PDF compile') does not hold.

### `src/pytex_api/_sandbox.py:143` — The sandbox image ships no biber, so every biblatex build inside the Podman sandbox fails

The Containerfile installs only tectonic and its shared libraries (`microdnf install ... && curl ... install -m 0755 tectonic`). It never installs biber. The preamble of every report and meeting protocol variant always loads `biblatex` (BASE_PACKAGES in src/pytex_hsrtreport/document.py:78), so tectonic calls `biber`. The 1.0.5 fix, `_biber_env`, runs only on the non-sandboxed branch of `compile_to_pdf` (src/pytex_api/_compile.py:353); the `_run_sandboxed` branch gets no biber on PATH, and the container runs with `--network none`, so it cannot download one. Failure scenario: `render_blob` with trust `sandboxed` (or `untrusted`) and `variant="report"` and output PDF stops with "Running external tool biber ... No such file or directory" and raises `CompileError`. The same defect hits `warm_sandbox_cache` (src/pytex_api/_sandbox.py:362), which compiles the real report and meeting protocol preambles inside that image, so `pytex-sandbox-init` fails on those samples.

### `src/pytex_api/_security.py:51` — _EVAL_COMMENT_RE misses eval comments that marko still parses, giving code execution on untrusted Markdown

The regex `^[ \t]*\[//\]:[ \t]*#.*$` demands a literal `[//]` and demands the `#` destination on the same line. marko normalizes the link-reference label and accepts a multi-line definition, and pytex_markdown.convert.block only tests `label == '//' and dest == '#'`, so three forms survive the strip and reach `eval(expr, pytex_namespace())`. Verified live against this tree with TrustLevel.UNTRUSTED and OutputKind.TEX: source `[ // ]: # "__import__('pathlib').Path('/tmp/x').write_text('pwned')"` and source `[//]:\n# "..."` both created /tmp/x. A tab-padded label `[\t//\t]:` works too. Since _render_markdown_source passes no policy to build_document, this strip is the only gate, so an untrusted Markdown blob runs arbitrary Python in the API process - no container, no rlimits, before any of them apply.

### `src/pytex_components/voting.py:77` — VotingResults.requires omits tikz although it nests a ColoredBox that requires it

`VotingResults.rendered` builds a `ColoredBox` and three `CustomBox` nodes inside the property, so their own `requires` sets never reach the package collector. The comment on lines 73-76 says exactly that, and re-declares `CALC` for that reason, but the returned set is `{MDFRAMED, XCOLOR, FONTAWESOME, MULTICOL, CALC}` while `ColoredBox.requires` (boxes.py:111) is `{MDFRAMED, XCOLOR, FONTAWESOME, CALC, TIKZ}`. `TIKZ` is dropped. A document whose only mdframed user is `VotingResults` renders a `\begin{mdframed}[...roundcorner=5pt...]` with no `\usepackage{tikz}` in the preamble, and the compile pass fails on the mdframed tikz framemethod.

### `src/pytex_hsrtreport/document.py:183` — Colors used only on the title page never get a \definecolor

`discovered_colors` walks only `self.body` and `self.user_preamble`. The `title`, `abstract`, `keywords` and `data_lines` values are rendered into the `TitlePage` node that `_body_parts` builds at line 247, so they are outside both walked roots. Build `HSRTReport(body="...", title="T", data_lines=(TitlePageDataLine("Betreuer", Textcolor(Color.hex("FF8800").name, "Prof. X")),))`: the rendered `.tex` contains `\textcolor{hexFF8800}{Prof. X}` on the title page but the preamble has no matching `\definecolor`, and tectonic aborts with "Undefined color `hexFF8800`".

### `src/pytex_hsrtreport/logos.py:51` — A custom logo path is an unrestricted file read, and untrusted frontmatter can set it

`logo_path` accepts any string that `Path(name).expanduser().is_file()` matches, with no confinement to a directory. `pytex_builder/variants.py:_logos` reads the `logos`/`logo` frontmatter key and `_resolve_logo` turns an existing path into an absolute path, and `pytex_api._render._render_markdown_source` calls `write_inline_logos(workdir)` in the host process for EVERY trust level (no chdir anywhere in `src/`). POST a Markdown build with `--trust-level untrusted` and the frontmatter `logo: /srv/pytex/secrets/report.pdf`: `write_inline_logos` copies those host bytes into `workdir/logos/report-<sha1>.pdf`, the title-page tikz overlay renders `\includegraphics[height=1.4cm]{logos/report-<sha1>.pdf}`, and the PDF returned to the caller embeds the first page of a file the caller must not see. Any host file with a `.pdf`, `.png`, `.jpg`, `.jpeg`, `.eps` or `.svg` suffix works. A path with another suffix raises `ValueError` from `IncludeImage.resolved_path`, and a missing path raises a different `ValueError` from `logo_path`, so the two errors also form a file-existence oracle.

### `src/pytex_markdown/convert.py:224` — Citation keys reach LaTeX unescaped although the postnote is escaped

`_CITE_KEY` (convert.py:122) admits `#`, `$`, `%` and `&`, and `_citation` passes the key straight into `Textcite(...)` / `Autocite(...)`. `pytex.commands.biblatex` wraps keys in `Parameter(",".join(keys))`, which renders a str verbatim. Verified: the prose `see @smith#2 now` renders `\textcite{smith#2}`, which aborts the compile pass with "Illegal parameter number in definition"; `see @a%b now` renders `\textcite{a%b}`, where `%` comments out the rest of the line and silently swallows the following text. The same function escapes the postnote on line 237 (`postnote=escape_latex(postnote)`), so the omission is inconsistent within one function.

### `src/pytex_markdown/convert.py:389` — A fenced code block can break out of lstlisting into live LaTeX

`_code` interpolates the raw Markdown code text into `Lstlisting(f"\n{code}\n", ...)` with no check for the environment terminator. Verified: the Markdown block ```` ```\ntext\n\end{lstlisting}\n\input{/etc/passwd}\n``` ```` renders `\begin{lstlisting}[breaklines=true]` / `text` / `\end{lstlisting}` / `\input{/etc/passwd}` / `\end{lstlisting}`. The `\input` executes as ordinary LaTeX and the stray `\end{lstlisting}` then errors out. Markdown is exactly the input `pytex_api` treats as untrustable, and `TrustPolicy.require_sandbox` (src/pytex_api/_policy.py:143) states that the in-process floor does not block `\input` of host files — only the Podman sandbox does. A document about LaTeX triggers this without any hostile intent.

### `src/pytex_markdown/protocol/convert.py:199` — Vote tally reads counts from the whole callout, not from the tally line

_vote_callout joins every line of the callout into `full` and then runs _tally on that single string. _TALLY_RE has no word boundaries, so the first `ja <digits>` anywhere in the callout wins. Input `> [!abstimmung] Antrag` / `> Es gab ja 2 Nachfragen` / `> Ja: 12, Nein: 3, Enthaltung: 1` yields yes=2 instead of 12. _is_tally_line already identifies the real tally line but is used only to filter the box body, never to scope the count search.

### `src/pytex_markdown/protocol/document.py:35` — Protocol parser omits the gfm extension, so protocol Markdown has no tables

`_PARSER = marko.Markdown()` builds a plain CommonMark parser, while `pytex_markdown/__init__.py:41` uses `marko.Markdown(extensions=["gfm"])`. Verified: parsing `| a | b |\n|---|---|\n| 1 | 2 |` with `_PARSER` yields `['Paragraph']`, with the gfm parser it yields `['Table']`. Every protocol built through `Protocol` / `IncludeProtocol` / `render_protocol` therefore loses pipe tables, strikethrough and autolinks. An agenda table in `sitzung.md` prints in the PDF as the literal text `| TOP | Thema | ...` instead of a tabularx. `MarkdownConverter._table` and the whole `COLUMN_ALIGN` table are dead code on this path, and nothing warns.

### `src/pytex_markdown/protocol/shortcodes.py:92` — {{vote}} summary prints U+00B7 directly, which tofus in the DIN font

_vote builds summary = f"Ja {yes} · Nein {no} · Enthaltung {abstain}" and passes it to Textcolor as a bare str. Parameter.rendered writes a str verbatim, so the separator never passes through pytex_markdown.glyphs. glyphs.GLYPH_NODES lists `·` as a character the bundled DIN font lacks, so `{{vote ja=12 nein=3}}` renders two blank tofu boxes in the PDF and issues no MissingGlyphWarning.

### `tests/pytex/commands/test_new_modules.py:257` — Newglossaryentry test never exercises the brace-wrapping guard the source calls out as a regression

src/pytex/commands/glossaries.py:35 carries an explicit regression comment: each field value is wrapped in braces (`f"{key}={{{value}}}"`) because the glossaries package otherwise reads a comma inside a value as a key-value separator, and "a description often contains a comma". The test at line 257 builds `Newglossaryentry("g1", {"name": "x", "description": "y"})` and asserts only `.rendered.startswith(r"\newglossaryentry{g1}{")`. Both chosen values are comma-free single characters, and the assertion stops before the field list. Concrete failure: if the join regressed to `f"{key}={value}"`, then `Newglossaryentry("acr", {"name": "GmbH", "description": "Gesellschaft, mit beschraenkter Haftung"})` renders `description=Gesellschaft, mit beschraenkter Haftung`, glossaries parses ` mit beschraenkter Haftung` as an unknown key and aborts the compile pass. The test stays green because `\newglossaryentry{g1}{` is still the prefix. The documented guard has zero coverage.

### `tests/pytex/model/test_color_extras.py:58` — test_tint_chain locks in a color name that xcolor cannot resolve

Color.tint() only appends `!<percent>` to the current name, so Color.named("blue").tint(50).tint(80) yields "blue!50!80" and the test asserts that string is correct. In an xcolor color expression the token after the second `!` must be a color name, so `blue!50!80` makes xcolor look up a color called `80` and the compile pass aborts with "Undefined color `80'". A user who chains two tints gets a green test suite and a failed PDF build. The correct chained result is a single tint (blue!40), or tint() should refuse a name that already contains `!`.

### `tests/pytex/model/test_color_extras.py:68` — test_collect_colors_unique_by_name uses two identical colors and hides an auto-name collision

collect_colors in src/pytex/model/color.py dedupes by `name` and keeps the first node. Color.rgb derives the default name from int(component * 255), so two different colors can get the same name. Verified: Color.rgb(0.5, 0.2, 0.1) and Color.rgb(0.501, 0.2, 0.1) both get the name "crgb127051025" with different specs, they compare unequal, and collect_colors(Concat(a, b)) returns exactly one Color carrying the spec 0.5,0.2,0.1. A document that uses both emits a single \definecolor and the second piece of text silently prints in the first color, with no error and no warning. The test proves dedupe only for two colors that are already equal, so it can never catch this.

### `tests/pytex/model/test_document_extras.py:60` — No test compares the path write_inline_images writes to with the path the rendered LaTeX references

Document.write_inline_images strips the root component (Path(*resolved.parts[1:])), while IncludeImage.rendered and filecontents_b64_block keep resolved_path.as_posix() unchanged. Verified with an absolute source /tmp/X/img.pdf and target_dir /tmp/X/build: write_inline_images returned /tmp/X/build/tmp/X/img.pdf, while the rendered document contains \includegraphics{/tmp/X/img.pdf} and \begin{filecontents*}...{/tmp/X/img.pdf.b64}. The written copy is therefore in a place the compile pass never looks. test_write_inline_images_creates_files only checks that the returned path exists and holds the source bytes, and test_rendered_emits_filecontents_before_document only checks the block order, so the two halves are never compared and the mismatch is invisible.

### `tests/pytex/model/test_length_chain.py:29` — test_chain_mixed_ops picks the one operator order that hides the missing parentheses

Length.__mul__, __truediv__ and __neg__ splice the operator onto the raw expression string with no parentheses. Verified in the dev shell: half = Textwidth() - Parindent(); (0.5 * half).rendered == "0.5\\textwidth-\\parindent", (-half).rendered == "-\\textwidth-\\parindent", (half / 2).rendered == "\\textwidth-\\parindent/2". The negation case is plainly wrong: -(textwidth - parindent) must be -textwidth + parindent, and the rendered LaTeX computes -textwidth - parindent, so a box laid out with it is off by two parindents. test_chain_mixed_ops writes 2 * Textwidth() - Linewidth() + "1cm", where the scalar hits an atomic length first, and test_double_neg negates an atom, so no test ever multiplies or negates a compound expression and the defect ships green.

### `tests/pytex/model/test_length_chain.py:57` — Length arithmetic tests assert calc syntax that no node requires

src/pytex/model/length.py builds `+`, `-` and `/` expressions and its own docstring says "the document must load calc. `Length` does not require calc on its own". `Length` returns no `requires`, and `Setlength` in src/pytex/commands/lengths.py just passes the expression through. Every test in test_length.py and test_length_chain.py asserts the rendered string and none asserts `.requires`, so the missing package requirement has no test at all. Concretely: Document(Setlength(r"\mylen", Linewidth() / 2)) renders \setlength{\mylen}{\linewidth/2} with no \usepackage{calc} in the preamble, and the compile pass aborts with "Illegal unit of measure (pt inserted)". The suite stays green because it never builds a document from a Length expression.

### `tests/pytex_components/test_boxes.py:106` — The concurrency test probably never runs the two render kinds at the same time

`test_concurrent_render_depth_isolation` submits all 500 `render_top_level` tasks before all 500 `render_deeply_nested` tasks. A `ThreadPoolExecutor` runs its queue in FIFO order, so with 8 workers every top-level render is finished before the first deep render starts. The overlap the test claims to exercise never happens. If the depth counter were reverted to a plain module global, the deep renders would still not be in flight while the top-level ones render, and the test would keep passing green while the race it guards is back.

## Severity medium

### `examples/mixed.tex.py:28` — IncludeMarkdown resolves its path against the working directory, so the example only runs from the repo root

`IncludeMarkdown` in src/pytex_markdown/__init__.py calls `Path(path).read_text(...)` with no anchoring to the input file. examples/mixed.tex.py passes the relative path "examples/notes.md". Running `cd examples && pytex mixed.tex.py --build` raises FileNotFoundError: 'examples/notes.md', even though the Markdown file sits right next to the `.tex.py` file. A user who follows the usual pattern of building from the document's own directory hits an error that names a path that does exist. Fixing it means resolving the path relative to the input file (or documenting the constraint in `IncludeMarkdown` itself); I only documented it in the example docstring.

### `src/pytex/commands/biblatex.py:30` — Printbibliography does not brace option values, so a comma in the title breaks the key-value list

opts is built as f"{key}={value}" with no braces. Printbibliography(title="Works cited, and more") renders \printbibliography[title=Works cited, and more]. biblatex splits the optional argument on the comma and treats "and more" as an unknown option, so the compile pass errors. glossaries.Newglossaryentry brackets the same hazard correctly with f"{key}={{{value}}}".

### `src/pytex/commands/builtin.py:410` — Cite's prenote argument actually renders as the postnote

Cite("a", prenote="p. 5") renders \cite[p. 5]{a}. Both standard LaTeX and biblatex read a single optional argument to \cite as the postnote, not the prenote. The comment in biblatex.py Autocite states this rule correctly for \autocite, so the two modules contradict each other. A caller who passes prenote="see" gets "[1, see]" instead of "[see 1]".

### `src/pytex/commands/builtin.py:545` — Verb does not reject a body that contains the delimiter, producing silently wrong output

`Verb(body, delim='|')` interpolates both without a check. `Verb('a|b')` renders `\verb|a|b|`. Verified render. LaTeX ends the verbatim text at the second bar, so it sets `a` in typewriter type and then `b|` in the running font — wrong output, no error, and the reader sees a plausible-looking line. A body holding a newline is louder but still a build failure: LaTeX aborts with "\verb ended by end of line". A user pasting a shell pipeline or a LaTeX alternation into `Verb` hits this on the first try, and the default delimiter is the character most likely to appear in such text.

### `src/pytex/commands/builtin.py:546` — Verb content is not verbatim: Raw defaults to allow_replacements=True, so an inline pytex(...) marker inside it executes

`Verb` wraps caller text in `Raw(...)` and takes the default `allow_replacements=True`, so `Raw.rendered` scans the content for `\iffalse{pytex(...)}\fi` and calls `eval` on any match. Verified: `Verb(r"\iffalse{pytex(Bold('x'))}\fi").rendered` is `\verb|\textbf{x}|` — the marker ran instead of printing. A document that uses `Verb` to show PyTeX marker syntax to a reader, which is the obvious use for a verbatim factory, gets its example evaluated and the wrong text printed. It is also a code-execution surface the caller did not ask for: `Verb` promises literal text. `Write18` (line 576) and `Def` (line 157) take the same default on caller-supplied text. Passing `allow_replacements=False` in `Verb` would restore the verbatim contract.

### `src/pytex/commands/builtin.py:585` — Whiledo declares no package requirement for ifthen

`\whiledo` is defined by the `ifthen` package, which `packages.py` already defines as `IFTHEN` on line 59. `Whiledo` carries no `@with_package`. Verified: `Whiledo('\\value{c}<5', 'x').requires` is `frozenset()`. A document whose only `ifthen` use is a `Whiledo` loop gets no `\usepackage{ifthen}` and the compile pass fails with "Undefined control sequence \whiledo". `Whiledo` is also unusable without `ifthen`'s `\ifthenelse` condition syntax, so the requirement is unconditional, not situational.

### `src/pytex/commands/builtin.py:590` — Foreach declares no package requirement for pgffor

\foreach comes from pgffor (or tikz). Foreach builds only Concat and Raw nodes, and neither carries a requires entry, so the preamble never loads the package. Verified: Foreach(r'\x', '1,2', 'y').requires is None. A document whose only pgffor use is Foreach fails the compile pass with "Undefined control sequence \foreach". packages.py already defines PGFFOR, and every other package-needing factory in this group uses @with_package.

### `src/pytex/commands/builtin.py:600` — BeginAccSupp and EndAccSupp declare no package requirement for accsupp

\BeginAccSupp and \EndAccSupp come from the accsupp package, which packages.py already defines as ACCSUPP. Verified: BeginAccSupp({'ActualText': 'x'}).requires is frozenset(). Using these factories for PDF accessibility text produces a rendered .tex file with no \usepackage{accsupp}, and the compile pass fails with "Undefined control sequence \BeginAccSupp".

### `src/pytex/commands/builtin.py:610` — Newglossarystyle declares no package requirement for glossaries

Every other glossaries command lives in glossaries.py behind @with_package(GLOSSARIES), but Newglossarystyle sits in builtin.py with no decorator. Verified: Newglossarystyle('s', 'b').requires is frozenset(). A document that defines a custom glossary style but does not also call Makeglossaries or Gls gets no \usepackage{glossaries} in the preamble, and the compile pass fails with "Undefined control sequence \newglossarystyle".

### `src/pytex/commands/counters.py:117` — UseCounter builds the \the macro by string concatenation, so a counter name with a digit renders the wrong macro

UseCounter returns Raw(f"\\the{name}"). TeX tokenizes a control sequence from letters only, so a name that is not all-letters splits. Newcounter("item2") is legal (LaTeX builds `\c@item2` and `\theitem2` through \csname), but UseCounter("item2") renders the text `\theitem2`, which TeX reads as `\theitem` followed by the literal character 2. The compile pass reports "Undefined control sequence \theitem" and, if `\theitem` happens to exist, silently prints the wrong value with a stray 2. Same failure for any counter name containing a digit, a hyphen or an underscore. Nothing validates `name`, and UseCounter("") renders the bare primitive `\the`.

### `src/pytex/commands/fontawesome.py:41` — FaIcon(None) returns a shared singleton whose parent is then overwritten

FaIcon returns the module-level `Empty` instance from pytex/model/empty.py:19. The @with_package wrapper builds WithPackage(Empty, FONTAWESOME), whose __post_init__ calls attach(self, Empty), and attach uses object.__setattr__ to write `_parent`. Two nodes that both use FaIcon(None) therefore share one object: the second call rewrites Empty._parent, so `.parent` and `.parents` on the first node's empty child point into the other node tree. Any pass that walks upward from an empty icon (or from Empty used elsewhere) reads the wrong ancestors.

### `src/pytex/commands/fontawesome.py:83` — FaVoteYea asks fontawesome v4 for an icon that only exists in v5

FaVoteYea renders `\faicon{vote-yea}`. The `vote-yea` icon entered Font Awesome at version 5.6; the v4.7 package this module pins (see the module docstring and the FaIcon comment) has no such name. The compile pass fails, or prints a missing-glyph box, for any protocol that shows a voting result. The test suite only asserts the rendered string, so it passes.

### `src/pytex/commands/fontspec.py:104` — Setfontfamilies renders a macro fontspec does not define

The factory emits `\setfontfamilies{Font}`. fontspec provides \setmainfont, \setsansfont, \setmonofont, \newfontfamily and \setfontfamily, but no plural \setfontfamilies. Any document that calls Setfontfamilies("Latin Modern Roman") compiles to "Undefined control sequence \setfontfamilies". Nothing in src/ or tests/ calls it, so the defect is invisible today.

### `src/pytex/commands/glossaries.py:61` — A dict-valued Parameter renders key=value with no braces, so a comma in any option value breaks the key-value list

`Parameter.rendered` (src/pytex/model/control_sequence.py:54) joins a dict as `f"{key}={value}"` with no braces around the value. Verified: `Printglossary({'title': 'Acronyms, and more'})` renders `\printglossary[title=Acronyms, and more]`. glossaries splits the optional argument on the comma and errors on the unknown option `and more`, so the compile pass fails. `Printacronyms` (line 72), `builtin.BeginAccSupp` (where `ActualText` is exactly the field most likely to hold a comma) and `biblatex.ExecuteBibliographyOptions` all take the same path. `Newglossaryentry`, 25 lines above in this same file, braces its values by hand with `f"{key}={{{value}}}"`, so the two option paths inside one module disagree.

### `src/pytex/commands/hooks.py:65` — AtBeginPage renders an undefined macro and requires no package

`\AtBeginPage` is not a LaTeX kernel macro, and the factory carries no @with_package. Neither atbegshi (`\AtBeginShipout`) nor everypage (`\AddEverypageHook`) defines that name. AtBeginPage(Raw("...")) placed in a preamble makes the compile pass stop with "Undefined control sequence". tests/pytex/commands/test_new_modules.py:436 only checks the rendered text.

### `src/pytex/commands/lengths.py:141` — Baselinestretch and Arraystretch_len are typed Length, but LaTeX defines them as macros holding a plain number

`_const` wraps the control sequence in `Length`, whose docstring says "Pass a `Length` anywhere a length is accepted, for example to `Vspace`, to `Setlength`". That holds for every other entry in this file, but `\baselinestretch` (line 141) and `\arraystretch` (line 196) are not dimen registers. LaTeX defines both as macros holding a bare number, set with `\renewcommand{\baselinestretch}{1.5}`. Verified: `Setlength('\\parskip', Baselinestretch()).rendered` is `\setlength{\parskip}{\baselinestretch}`. `\baselinestretch` expands to `1`, a number with no unit, and the compile pass aborts with "Illegal unit of measure (pt inserted)". The `Length` operators fail the same way: `0.5 * Arraystretch_len()` yields the expression `0.5\arraystretch`, which is not a dimension. The type invites exactly the call that cannot work.

### `src/pytex/commands/lengths.py:196` — Arraystretch_len and Baselinestretch return a Length, but \arraystretch and \baselinestretch are macros, not length registers

LaTeX defines both as macros that hold a plain number (`\def\arraystretch{1}`), so neither works where a length is expected. Writing to them fails: `Setlength('\\arraystretch', '1.5')` renders `\setlength{\arraystretch}{1.5}` and the compile pass aborts with "Missing number, treated as zero". Reading them fails too: `Vspace(Arraystretch_len())` renders `\vspace{\arraystretch}` and aborts with "Illegal unit of measure (pt inserted)". Verified render: `Setlength('x', Arraystretch_len())` -> `\setlength{x}{\arraystretch}`. Every other entry in this module is a real length register, so these two look usable and are not. `Renewcommand` is the correct route, which is the same conclusion as the already-reported `tables.Arraystretch` bug — the length module carries the mirror image of it.

### `src/pytex/commands/listings.py:21` — _render_value flattens a TeX option value to a string, dropping its package requirements

_opts_to_str wraps the joined result in Raw(...), and _render_value turns each TeX value into a bare string via `.rendered`. The original node never enters the node tree, so the preamble collector never sees its `requires`. Lstset({"keywordstyle": SelectColor("blue")}) renders `\lstset{keywordstyle=\color{blue}}` while xcolor is absent from the preamble, and the compile pass fails with "Undefined control sequence \color". Lstdefinestyle (line 47) has the same defect. Note that `Parameter` keeps a TeX value as a real child node, so every other factory in this group preserves requirements - listings is the outlier.

### `src/pytex/commands/tables.py:110` — Newcolumntype and Arraybackslash declare no package requirement for array

`\newcolumntype` and `\arraybackslash` both come from the `array` package, which `packages.py` already defines as `ARRAY` on line 30. Neither factory carries `@with_package`, although `Tabularx`, `Longtable`, `Multirow` and the booktabs rules in the same file all do. Verified: `Newcolumntype('C', None, 'p{2cm}').requires` is `frozenset()` and `Arraybackslash().requires` is `frozenset()`. A document that defines a centered fixed-width column with `Newcolumntype('C', None, '>{\\centering\\arraybackslash}p{3cm}')` and then uses it in a plain `Tabular` gets no `\usepackage{array}` in the preamble, and the compile pass fails with "Undefined control sequence \newcolumntype". The failure hides whenever the document also loads `tabularx`, which pulls `array` in, so it appears only in the plain-`tabular` case.

### `src/pytex/helpers/coerce.py:22` — coerce_tex wraps any non-TeX value in Raw, so a non-string fails at render time in an unrelated module

`coerce_tex` tests `isinstance(value, TeX)` and otherwise returns `Raw(value)` with no string check, even though the annotation says `TeX | str`. `Raw.content` then holds a non-string and the failure surfaces only inside `Raw.rendered`, whose guard is `"\\iffalse" not in self.content`. Verified: `Concat('Page ', 5).rendered` raises `TypeError: argument of type 'int' is not iterable` from raw.py, with nothing in the traceback naming the caller that passed the int. The path is easy to reach from real input — a YAML frontmatter value parsed as an int or a float flows into `Concat`, `Parameter`, or `Document(body=...)` through `coerce_tex` — and the build dies at render with a message that points at the wrong module.

### `src/pytex/helpers/parenting.py:22` — attach() silently re-parents an already-attached node, so reusing one node instance corrupts the parent chain

`attach` overwrites `_parent` with no check for an existing parent and no copy of the child. Nodes are ordinary values that a `.tex.py` file naturally reuses. With `caption = Bold('Figure 1')` and `Document(body=Concat(caption, Environment('figure', caption)))`, `Concat.__new__` attaches `caption` to the `Concat`, then the `Environment` attaches the same instance to itself; whichever `attach` runs last wins. `caption.parents` then reports exactly one of the two positions, so a check that walks upward from that node misses the other placement entirely, while `rendered` still emits the node twice. There is no warning and no exception — the tree is silently a DAG that presents itself as a tree.

### `src/pytex/helpers/sanitize.py:38` — Comment claims PyTeX always loads babel with `ngerman`, but no core package requirement pulls babel in

The comment that justifies the `"` -> `\textquotedbl{}` mapping asserts that babel with `ngerman` is always loaded, which is what makes `"` an active shorthand character. Grepping the tree shows `BABEL` is referenced only by src/pytex/packages.py (its definition and the enum) and src/pytex_hsrtreport/document.py:90. `pytex.model.document.Document` adds no default package, so a plain `Document(body=Sanitize(text))` renders a preamble with no `\usepackage[ngerman]{babel}` at all. The stated premise is false for every document that is not an hsrtreport document. The concrete cost is a maintainer decision: reading this comment, someone who extends `ESCAPES` assumes babel's German shorthands (`"a`, `"=`, `"`) are active everywhere, and adds or omits escapes on that wrong basis.

### `src/pytex/model/color.py:126` — Color.rgb writes the raw Python float repr into the spec, so a small component renders as scientific notation

`ColorSpec("rgb", f"{r},{g},{b}")` uses `str(float)`, which switches to exponent form below 1e-4. Verified: `Color.rgb(1e-07, 0.0, 0.0).spec` is `ColorSpec(model='rgb', value='1e-07,0.0,0.0')`. The preamble then renders `\definecolor{crgb000000000}{rgb}{1e-07,0.0,0.0}`. TeX cannot parse `1e-07` as a number, so the compile pass aborts with "Missing number, treated as zero" inside xcolor. The same happens for any component a computation produces below 0.0001, for example a normalized value scaled from a data series.

### `src/pytex/model/comment.py:30` — Comment does not reject a newline in `text`, so the tail escapes the comment and becomes live LaTeX

`rendered` returns `f"%{self.text}\n"` and never checks `text` for a line break. Verified: `Comment('line1\nline2').rendered` is `'%line1\nline2\n'`. Only `line1` is a comment. `line2` reaches the compile pass as document body text. When the comment text comes from data rather than a literal — a Markdown frontmatter value, a filename, a `--config` string — this is a LaTeX injection: `Comment('note\n\\input{/etc/passwd}')` renders a real `\input`. A multi-line comment also silently loses its `%` on every line after the first, so the intended comment appears in the PDF.

### `src/pytex/model/concat.py:30` — Concat returns the shared Empty singleton, whose `_parent` is then global mutable state

`Concat()` with no surviving child returns the module-level singleton `Empty` from `empty.py`, and `Document.preamble` also defaults to that same singleton. `Document.__post_init__` calls `attach(self, self.body, self.preamble)`, which does `object.__setattr__(Empty, "_parent", self)`. Build two documents in one process and the second overwrites the first: `doc_a.children[0].parent is doc_b`. Any code that walks upward via `TeX.parents` from an empty preamble or an empty `Concat` reaches the wrong root node.

### `src/pytex/model/concat.py:47` — attach overwrites `_parent`, so a node reused in two trees reports only the last parent

`Concat.__new__` calls `attach(instance, *coerced)`, which does `object.__setattr__(child, "_parent", parent)` with no check for an existing parent and no copy of the child. Verified: `x = Raw('shared'); c1 = Concat(x, Raw('a')); c2 = Concat(x, Raw('b'))` leaves `x.parent is c2` and `x.parent is c1` False. Binding a node to a variable and using it twice is the natural way to reuse a header, a signature block or a logo. Any code that walks upward through `TeX.parents` from the reused node — the analysis pass looking for the owning `Document`, or a component that reads its enclosing environment — gets the wrong root node for every tree except the last one built. Rendering still works, so the fault is silent.

### `src/pytex/model/document.py:73` — ordered_packages never checks `incompatible`, so conflicting packages both render

`Package` stores `_incompatible`, `amend` merges into it, `DefinePackage` accepts it, and `PackageProtocol` documents it as "The packages that LaTeX must not load with this one". Nothing reads it: a grep for `incompatible` across `src/` finds only the declaration sites in `package.py` and `interface/package.py`. `ordered_packages` sorts on `after` alone. So `DefinePackage("subfig", incompatible={SUBCAPTION})` followed by a document whose node tree requires both renders `\usepackage{subcaption}` and `\usepackage{subfig}` next to each other. The compile pass fails deep inside the two packages with a redefinition error, and nothing points back at the declared conflict. The declared constraint is dead data.

### `src/pytex/model/document.py:127` — write_inline_images can write outside target_dir via a relative path with `..`

The code strips the root only for absolute paths: `rel = Path(*resolved.parts[1:]) if resolved.is_absolute() else resolved`. A relative source such as `IncludeImage("../../etc/logo.png", inline_base64=True)` keeps its `..` segments, so `dest = Path(target_dir) / "../../etc/logo.png"` and `dest.write_bytes(...)` writes two levels above the build directory. For an untrusted input file this is an arbitrary-file-write outside the intended output area.

### `src/pytex/model/document.py:141` — Core Document never renders `\definecolor`, so any Color with a spec breaks the build

`Document.rendered` concatenates the document class, the ordered packages, the inline image block, the preamble and the document environment. It never calls `collect_colors`, and no `\definecolor` line appears anywhere in `pytex.model`. Only `pytex_hsrtreport.document` does that work. So `Document(body=TextColor(Color("#FF0000"), "hi"))` renders `{\color{cFF0000}hi}` with no definition, and the compile pass fails. `collect_colors` is public API in `pytex.model.color.__all__` but the core `Document` does not use it.

### `src/pytex/model/document_class.py:12` — Document class options render in nondeterministic order

`_render_options` joins a `set[PackageOption]`. Python randomizes str hashing per process (PYTHONHASHSEED), so `DocumentClass("scrreprt", {"a4paper", "12pt", "twoside"})` renders `\documentclass[a4paper,12pt,twoside]{scrreprt}` in one run and `\documentclass[12pt,twoside,a4paper]{scrreprt}` in the next. The rendered `.tex` file is therefore not reproducible, which contradicts the effort `ordered_packages` makes to break ties by name for exactly that reason. `Package._options_string` (package.py:93) has the identical defect for `\usepackage` options.

### `src/pytex/model/image.py:89` — SVG conversion target is hardcoded to a literal `build` directory relative to the cwd

`resolved_path` returns `Path("build") / f"{src.stem}-{digest}.pdf"` and ignores `--build-dir` entirely. Run `pytex doc.tex.py --build --build-dir /tmp/out` from a read-only checkout and `_convert_to_pdf` calls `dst.parent.mkdir(parents=True)` on `./build`, which raises PermissionError. When it does succeed, the converted PDF lands next to the input file rather than in the build directory, and the `\includegraphics{build/logo-ab12cd34ef.pdf}` path only resolves if the compile pass happens to run from the same cwd.

### `src/pytex/model/include.py:25` — IncludeTeX reads the file with the locale encoding instead of UTF-8

`Path(path).read_text()` passes no `encoding`, so Python uses `locale.getencoding()`. This project renders German documents whose `.tex` fragments contain umlauts. On a machine or CI container with LANG=C or POSIX (ASCII default), `IncludeTeX("kapitel.tex")` on a UTF-8 file raises `UnicodeDecodeError: 'ascii' codec can't decode byte 0xc3`, while the same file works on a UTF-8 host. The result depends on the environment, not on the input.

### `src/pytex/model/length.py:18` — Length uses calc syntax but never declares calc as a package requirement

`Length` inherits the default `TeX.requires`, which returns None. `Setlength("\\parindent", Linewidth() - "0.5cm")` renders `\setlength{\parindent}{\linewidth-0.5cm}`. Without `\usepackage{calc}` in the preamble, LaTeX reports "Illegal unit of measure (pt inserted)" and the compile pass fails. Nothing in the node tree causes calc to load, so the author must remember `extra_packages` by hand.

### `src/pytex/model/length.py:51` — Length arithmetic never parenthesizes, so multiply, divide and negate produce wrong LaTeX

`__mul__` returns `Length(f"{factor}{self.expr}")`. For `l = Length("\\textwidth") + "1cm"` (expr `\textwidth+1cm`), `0.5 * l` renders `0.5\textwidth+1cm`, which calc evaluates as `(0.5*\textwidth) + 1cm` instead of `0.5*(\textwidth+1cm)`. `__truediv__` gives `\textwidth+1cm/2` and `__neg__` gives `-\textwidth+1cm`, both wrong by the same reasoning. Any composite `Length` passed through a scale or a negation silently produces a wrong page dimension.

### `src/pytex/model/length.py:145` — Length multiplication and division do not parenthesize the operand, so precedence is lost

`__mul__` renders `f"{factor}{self.expr}"` and `__truediv__` renders `f"{self.expr}/{divisor}"`, neither wrapping an expression that is already a sum. Verified: `0.5 * (Textwidth() - '1cm')` renders `0.5\textwidth-1cm`. Under calc that is half the text width minus a whole centimeter, not half of the difference. `Setlength('\\mybox', 0.5 * (Textwidth() - '2cm'))` gives a box 1cm too wide with no error at all — the page just comes out subtly wrong. `(Textwidth() + '1cm') / 2` renders `\textwidth+1cm/2` with the same defect. This is reachable only through the `lengths` factories, which are the public surface for `Length`.

### `src/pytex/model/package.py:84` — Package.__post_init__ never runs, so the duplicate-instance warning is dead code

Package is a plain class with a hand-written __init__, not a dataclass, so Python never calls __post_init__. The PACKAGES[self.name] registration and the "Multiple Instances of {name} in circulation!" warning inside it never execute. Constructing Package("amsmath") directly (which coerce_package does for every string) produces a second, unregistered instance and no diagnostic is logged, hiding the with_package.py:24 defect above.

### `src/pytex/model/package.py:143` — DefinePackage silently drops `options` for an existing name, and `amend` offers no way to add them

When `name` is already in `PACKAGES`, `DefinePackage` calls `amend(after=..., incompatible=...)` and returns early. `amend` takes no `options` parameter, so the `options` argument is discarded. `pytex/packages.py:22` runs `XCOLOR = DefinePackage("xcolor")` at import time, so every later call loses its options. Verified: `DefinePackage('xcolor'); p = DefinePackage('xcolor', options={'table'})` gives `p.options == frozenset()` and `p.rendered == '\\usepackage{xcolor}'`. A document that needs `\usepackage[table]{xcolor}` for `\rowcolors` renders plain xcolor, and the compile pass fails with "Undefined control sequence \rowcolors". No error and no warning marks the dropped option.

### `src/pytex/model/raw.py:26` — PATTERN requires balanced parentheses, so a marker whose Python code holds an unbalanced paren inside a string never matches

`_nested_inner` builds `(?:[^()]|\(...\))*`, which can only match parentheses that balance. A Python string literal inside the expression may hold a lone paren. Verified with the real `PATTERN`: `\iffalse{pytex(Raw("x"))}\fi` matches, but `\iffalse{pytex(Raw("(a"))}\fi` does not. `Raw.rendered` therefore returns the content unchanged and the literal `\iffalse{pytex(Raw("(a"))}\fi` lands in the rendered `.tex` file. There is no warning. This is a different failure from the depth-8 nesting limit: the expression here is one level deep and still fails, and any caption or label text containing a smiley or a single parenthesis triggers it.

### `src/pytex/packages.py:53` — TIKZ_LIB_ARROWS and TIKZ_LIB_POSITIONING name TikZ libraries as if they were packages

DefinePackage("tikz-arrows") and DefinePackage("tikz-positioning") (line 104) render as `\usepackage{tikz-arrows}` and `\usepackage{tikz-positioning}`. Neither .sty file exists on CTAN; TikZ libraries load with `\usetikzlibrary{arrows}` / `\usetikzlibrary{positioning}`. Any node that adds one of these as a package requirement makes tectonic abort the first compile pass with "LaTeX Error: File `tikz-arrows.sty' not found". Both names are exported public API, and neither appears in the Packages enum, so the enum and the module constants disagree.

### `src/pytex/packages.py:94` — KOMA_SCRIPT and ALGORITHMS name bundles that have no .sty file

DefinePackage("koma-script") renders `\usepackage{koma-script}`, but koma-script is a bundle whose members are scrartcl/scrreprt/scrbook document classes and typearea.sty; koma-script.sty does not exist. DefinePackage("algorithms") (line 84) has the same problem: the algorithms bundle ships algorithm.sty and algorithmic.sty, not algorithms.sty. A node that requires either constant makes tectonic abort with "File `koma-script.sty' not found". KOMA_SCRIPT is also reachable through Packages.KOMA_SCRIPT.

### `src/pytex/template.py:96` — The module docstring promises that iterables are recursed, but `_coerce` handles only list and tuple

Rule 2 of the committed module docstring says interpolations are "recursed when they are nested template strings or iterables of the above", while `_coerce` tests only `isinstance(value, (list, tuple))`. A generator, a set, `dict.values()`, or any other iterable falls through to `format(value, spec)` and is escaped. Failure: `tex(t"{(Bold(n) for n in names)}")` writes the literal text `<generator object <genexpr> at 0x7f...>` into the rendered `.tex` file instead of concatenating the `Bold` nodes; `tex(t"{ {Bold(a), Bold(b)} }")` behaves the same way. The document still compiles, so the wrong text reaches the PDF with no error.

### `src/pytex_analyze/optimize.py:172` — Optimize evaluates every inline `pytex(...)` marker three extra times

For one `Raw` holding one marker, `_tokenize` evaluates it once in `_token_node` (line 172), once more via `candidate.rendered` (line 179), and once more via `target = raw.rendered` (line 180); `_native` then evaluates it again at line 135 when tokenization returns None. Verified with a counter callable: a single `Optimize(Raw(r'x \iffalse{pytex(bump())}\fi y', namespace={'bump': bump}))` produced 3 calls, and reading `.rendered` on the result produced a 4th, so the document printed `x 4 y` where an unoptimized render prints `x 1 y`. Any marker that is not a pure function of its inputs — a figure counter, a `next(iterator)`, an appended log line, a file write — produces the wrong value in the rendered `.tex` file and repeats its side effect four times per build.

### `src/pytex_analyze/optimize.py:181` — The math-whitespace exception in the tokenizer guard rewrites `\[..\]` inside a verbatim environment

`_tokenize` accepts a candidate when `_strip_math_ws(rendered) == _strip_math_ws(target)`. `_strip_math_ws` is purely textual and does not know whether the `\[` it found is in math mode or inside `verbatim`, `lstlisting` or a `\verb` argument, where TeX prints whitespace literally. Verified: `Optimize(Raw('\\begin{verbatim}\n\\[  x + 1  \\]\n\\end{verbatim}'))` renders `\begin{verbatim}\n\[x + 1\]\n\end{verbatim}` — the two-space padding is gone from the rendered `.tex` file, so a code listing that demonstrates LaTeX math source is printed with different spacing than the author wrote.

### `src/pytex_api/__init__.py:165` — render_blob silently drops caller-supplied assets for TEX-only output

In render_blob, `assets = filter_assets(req.assets)` only validates asset names; the validated dict is passed on to compile_to_pdf (line 183), which is the only place that ever writes those bytes to disk (src/pytex_api/_compile.py, the `for name, data in assets.items(): (workdir / name).write_bytes(data)` loop inside compile_to_pdf). When `req.output_kind is OutputKind.TEX`, render_blob returns early without ever calling compile_to_pdf. Concrete failure: a caller sends BuildRequest(source=<markdown referencing an image>, input_kind=MARKDOWN, output_kind=OutputKind.TEX, assets={'logo.png': <bytes>}) expecting a .tex file that references logo.png. The name passes validation, but logo.png is never written to any directory and is not returned in BuildResult (BuildResult.output is only the .tex text). The caller has no way to retrieve the asset bytes they supplied, and if they later feed the returned .tex to a LaTeX compiler expecting logo.png alongside it, that compile fails with a missing-file error that pytex_api gave no warning about.

### `src/pytex_api/_compile.py:226` — _should_sandbox skips the image-present check when tectonic_in_image is False

The expression is `not config.tectonic_in_image or sandbox_image_present(config.image)`. With `SandboxConfig(tectonic_in_image=False)` it short-circuits to True without ever checking that the image exists locally, which contradicts the original docstring promise of 'never pulling at request time'. Failure: a caller passes `SandboxConfig(tectonic_in_image=False, image='registry.example/pytex-tectonic:latest')` and the image is not local. A `sandboxed` PDF request then reaches `_run_sandboxed`, and `podman run` attempts a registry resolve/pull inside the request, so an untrusted request drives outbound network traffic and the build fails with an opaque podman error instead of the fail-closed CompileError.

### `src/pytex_api/_compile.py:323` — An asset ending in .sty shadows an allowlisted package in the compile directory

Assets land in the same directory that tectonic runs in, and TeX searches the current directory before the bundle. validate_asset_name accepts 'tikz.sty'. Failure: an untrusted request sends source that uses tikz (allowlisted, so enforce_packages passes) plus assets={'tikz.sty': b'<attacker macros>'}. tectonic loads the caller's tikz.sty instead of the bundle one, so the package allowlist decides only the *name* that may be loaded, never the code behind it. The attacker macros then run with whatever surface LaTeX has inside the container (\\openin/\\input of /cache and of the read-only host font mounts, \\write to the work directory).

### `src/pytex_api/_compile.py:323` — An asset named 'build' raises IsADirectoryError, which escapes as a non-ApiError

build_dir = workdir/'build' is created at line 320-321, and the asset loop at 322-323 then calls (workdir/'build').write_bytes(data). validate_asset_name accepts 'build'. Verified: the write raises IsADirectoryError [Errno 21]. _render_or_compile_error wraps only render_to_latex, not compile_to_pdf, so nothing in render_blob maps this to an ApiError - the caller gets a raw IsADirectoryError instead of the documented TrustError/LimitError/CompileError, and a server that catches ApiError to build a 4xx returns a blanket 500 with the temp path in the traceback.

### `src/pytex_api/_compile.py:339` — The in-process rlimit floor is never applied to any build render_blob can produce

`policy_for` returns `require_sandbox == apply_rlimits` for all three trust levels, so the `elif policy.require_sandbox: raise` branch swallows every non-trusted build and the `else` branch is reached only for `trusted`, where `apply_rlimits` is False. Result: `make_rlimit_preexec` is dead for anything routed through `render_blob`, the `console.warn` about weaker confinement is unreachable, and `BuildLimits.cpu_timeout_s` is enforced nowhere at all (the podman path passes `--cpus`, a share, not an RLIMIT_CPU). Failure: a caller sets `cpu_timeout_s=1` on an untrusted PDF request; a document that spins CPU inside the container runs until `wall_timeout_s` (default 30s) instead of being SIGXCPU'd after 1s.

### `src/pytex_api/_render.py:51` — Concurrent TEX_PY renders race on the global sys.path via get_tex_node

`get_tex_node` calls `pytex_builder.render._render_python`, which does `sys.path.insert(0, workdir)` and `sys.path.pop(0)` around `exec_module`. `render_blob_async` runs builds in the default thread-pool executor, so two `TEX_PY` requests overlap in one process. Failure: thread A inserts its temp dir, thread B inserts its own, A finishes and pops index 0 which removes B's entry, then B pops index 0 which removes A's already-gone entry; B's own sibling imports then fail with ModuleNotFoundError, and during the overlap B can import a sibling module out of A's temp directory instead of its own.

### `src/pytex_api/_sandbox.py:222` — sandbox_image_present runs podman with no timeout on every PDF request

`subprocess.run(['podman','image','exists',image], capture_output=True, check=False)` has no timeout=, and _should_sandbox calls it for every non-trusted PDF build. build_sandbox_image and warm_sandbox_cache both take timeout_s; this one, the only call on the request path, does not. Failure: another podman operation holds the container-storage lock (a common state after a killed build, and _run_sandboxed's own untimed `podman rm -f` can create it). `podman image exists` then blocks indefinitely, the executor thread that ran render_blob is pinned, render_blob never reaches its `finally: shutil.rmtree(workdir)`, and req.limits.wall_timeout_s never applies because the process has not started yet.

### `src/pytex_api/_security.py:98` — enforce_packages scans only the rendered LaTeX, not caller assets pulled in with \input

enforce_packages runs on the rendered LaTeX string inside render_to_latex (_render.py:144). Caller assets are written into the same workdir later (_compile.py:322) and are never scanned. Concrete failure: an untrusted BuildRequest with input_kind=TEX, source=b"\\input{evil}" and assets={"evil.tex": b"\\usepackage{minted}"} gets the source scanned (it names no package, so it passes) while evil.tex reaches the tectonic binary unscanned. The allowlist is defeated for anything a document can \input. Remaining defenses are the Podman sandbox, --only-cached and shell-escape off, so this is defense-in-depth loss rather than direct code execution.

### `src/pytex_api/sandbox_init.py:225` — main catches only RuntimeError, so a podman timeout escapes as a traceback

build_sandbox_image and warm_sandbox_cache both pass timeout_s=600.0 to subprocess.run, which raises subprocess.TimeoutExpired. TimeoutExpired subclasses SubprocessError, not RuntimeError (confirmed: issubclass(subprocess.TimeoutExpired, RuntimeError) is False). Failure: a user on a slow link runs `pytex-sandbox-init`; the bundle warm-up exceeds 600s. Instead of console.error('sandbox initialisation failed') plus the _friendly_error hint and exit code 1 - the whole point of this script - the user gets an unhandled TimeoutExpired traceback and a non-zero exit from SystemExit, with no hint about what to do. The same applies to `podman build` on a slow registry.

### `src/pytex_builder/build.py:92` — _default_output does not strip the `.py` part of a `.py.tex` input

`_default_output` strips one `.py` or `.tex` suffix, then a second suffix only when it is `.tex`. For the `name.tex.py` convention that works. For the `name.py.tex` convention it strips `.tex` and leaves `.py`. `_default_output(Path('examples/replacements.py.tex'), Path('build'))` returns `build/replacements.py.out.tex` (verified by running it), so the TeX jobname becomes `replacements.py.out` and the PDF becomes `build/replacements.py.out.pdf`. The docstring of examples/replacements.py.tex promises `replacements.out.tex` and `build/replacements.out.pdf`.

### `src/pytex_builder/build.py:95` — _default_output does not strip the `.py` part of a `.py.tex` input

Confirmed by tracing and by replaying the function body. Line 93 strips one `.py` or `.tex` suffix. Line 95 then strips a second suffix only when that suffix is `.tex`. For `name.tex.py` the two steps work. For `name.py.tex` the first step strips `.tex` and leaves `.py`, and the second test fails. `_default_output(Path('examples/replacements.py.tex'), Path('build'))` returns `build/replacements.py.out.tex`, so the TeX jobname is `replacements.py.out` and the PDF is `build/replacements.py.out.pdf`. The docstring of examples/replacements.py.tex promises `replacements.out.tex` and `build/replacements.out.pdf`. Not fixed, as instructed.

### `src/pytex_builder/build.py:426` — MAX_PASSES = 3 is dead; the build never runs a third compile pass

The loop `for pass_no in range(1, MAX_PASSES + 1)` only calls `run_makeindex` when `pass_no == 1`, and unconditionally `break`s otherwise. So the build runs at most 2 compile passes even though MAX_PASSES is 3. Failure scenario: a document with `glossaries` where the `.glo` file is only produced by the *second* compile pass (e.g. a glossary entry that is first referenced from a `\chapter` title that itself only settles after the ToC pass). Pass 1 finds no `.glo`, `run_makeindex` returns False, the loop breaks, and the PDF ships with '??' for every glossary/acronym reference. The same holds for a cross-reference that needs three passes to converge: the third pass never happens and the PDF contains stale page/section numbers with no warning.

### `src/pytex_builder/render.py:108` — Markdown input is read, and the rendered .tex written, with the locale encoding instead of UTF-8

`_render_markdown` calls `path.read_text()` and `build.py:404` calls `output.write_text(source)`, both without `encoding=`. Python then uses the locale encoding. The same repository passes `encoding="utf-8"` explicitly two functions away (`render.py:59`, `variants.py:220`), so the omission is inconsistent, not a convention. Build a German protocol containing `Gäste` on a Windows host (locale encoding cp1252): the UTF-8 bytes 0xC3 0xA4 decode as two cp1252 characters, so the title page prints `GÃ¤ste` with no error at all. On a host whose locale encoding is latin-1, `output.write_text` instead raises UnicodeEncodeError for any character outside latin-1 (for example the `…` that `tree.py:_short` can put into a Raw, or a `→` in the Markdown), and `main()` catches only BuildError and KeyboardInterrupt, so the user gets a raw traceback and exit code 1.

### `src/pytex_builder/tectonic.py:173` — The tectonic auto-download cannot work on Windows, but CI ships a Windows binary

CONFIRMED. `ensure_tectonic` returns early for a tectonic binary on PATH (line 158) and for the cache (line 163). Otherwise line 173 demands both `curl` and `sh` on PATH and line 186 runs `curl ... | sh` with `shell=True`. Windows has no `sh`, so the function always raises BuildError there. `_cached_binary()` (line 153) returns `CACHE_DIR / "tectonic"` with no `.exe` suffix, so a hand-placed Windows binary in the cache is not found either. The `binaries` matrix in .github/workflows/release.yml publishes `pytex-windows-x86_64.exe`, and its smoke test only renders (no `--build`), so CI never sees the failure. A Windows user who runs `pytex doc.tex.py --build` with no tectonic on PATH gets "tectonic is not installed and cannot be downloaded without 'curl' and 'sh' on PATH", even with a working curl.

### `src/pytex_builder/tectonic.py:186` — The tectonic auto-download cannot work on Windows, but CI ships a Windows binary

`ensure_tectonic` requires both `curl` and `sh` on PATH (line 173) and then runs `curl ... | sh` through a POSIX shell (line 186). Windows has no `sh`, so on Windows the function always raises BuildError instead of downloading. `_cached_binary()` (line 153) also returns `CACHE_DIR / "tectonic"` with no `.exe` suffix, so a manually placed Windows binary in the cache is not found either. The `binaries` job in .github/workflows/release.yml builds and publishes `pytex-windows-x86_64.exe`, and its smoke test only renders (no `--build`), so the failure never shows up in CI. A Windows user who runs `pytex doc.tex.py --build` without tectonic already on PATH gets "tectonic is not installed and cannot be downloaded without 'curl' and 'sh' on PATH", even on a machine with working curl.

### `src/pytex_builder/tectonic.py:352` — subprocess.TimeoutExpired from _biber_runs escapes as an unhandled exception

_biber_runs calls subprocess.run([...], timeout=30) but catches only OSError; subprocess.TimeoutExpired is a SubprocessError, not an OSError. If a cached biber hangs (a corrupt binary that blocks, or an NFS-stalled cache path), the `if _biber_runs(cached)` call at line 352 sits outside _ensure_biber's try block, so TimeoutExpired propagates out of run_tectonic. main() catches only BuildError and KeyboardInterrupt, so the user gets a raw traceback instead of a build error message and exit code 1.

### `src/pytex_builder/tectonic.py:419` — biber 2.20 and 2.21 are downloaded with no checksum verification

BCF_TO_BIBER maps '3.11'->'2.20' and '3.12'->'2.21', but BIBER_SHA256 only has entries for 2.11-2.19 and the mirror only hosts those assets. Compile a document whose .bcf reports version 3.12: _ensure_biber('2.21') builds asset name 'biber-2.21-linux_x86_64-musl.tar.gz', BIBER_SHA256.get returns None, the mirror URL 404s, and the SourceForge URL is then downloaded with sha=None, so _download_to skips the integrity check entirely and the unverified binary is chmod 0755 and executed. The comment above BIBER_SHA256 claims every mirrored platform is covered, which hides the gap.

### `src/pytex_builder/tectonic.py:508` — probe_bcf runs a full extra tectonic compile on every pass of every non-biblatex document

run_tectonic calls biber_for_build, and when it returns None it runs probe_bcf(cmd), which is a complete extra tectonic invocation. A document that uses no biblatex never produces a .bcf file, so biber_for_build returns None on every compile pass, forever. Build a plain Markdown or .tex document with `pytex doc.md --build`: tectonic runs twice per compile pass (probe + real), roughly doubling build time, and the second biber_for_build call after the probe still returns None. The same happens permanently for any document whose BCF format version is not a key of BCF_TO_BIBER (e.g. BCF 3.13 from a newer biblatex), because that path also returns None.

### `src/pytex_builder/variants.py:187` — _protocol drops --config and classoptions; the module docstring promises the opposite

`build_document` merges frontmatter and `--config` into `options`, but `_protocol` forwards only `meta` to `build_protocol` and reads `options` for the title alone. `build_protocol` then derives everything from `meta`: `_variant(meta)`, `_title(meta)`, `_data_lines(meta)`, `signature_block_from_meta(meta)` and `ProtocolConverter(meta=meta)`. Run `pytex notes.md --config '{"gremium": "stupa"}'`: `_auto` sees `gremium` in `options` and routes to the protocol builder, but `_variant(meta)` sees no `gremium`, so the protocol renders with the default logos and an auto-composed title that ignores the committee. `_class_options(options)` is not passed at all, so a `classoptions` frontmatter key is silently ignored for both protocol variants. The module docstring states without qualification that document-class parameters come from the frontmatter and from `--config`, and that `--config` overrides the frontmatter.

### `src/pytex_builder/variants.py:329` — _derive_title matches a `#` line inside a fenced code block, steals it as the title and deletes it from the body

`_H1_RE = ^#\s+(.+?)\s*#*\s*$` is applied line by line with no awareness of ``` fences, and `_derive_title` deletes the first matching line from the body. Render a README-style document whose frontmatter has no `title` and whose first heading is `## Setup`, followed by a fenced shell block containing `# Install the tool`: I ran it and `_derive_title` returns `('Install the tool', ...)` with that line removed. The PDF title page reads 'Install the tool' and the code block in the body silently loses its comment line. This is content loss, not just a wrong title.

### `src/pytex_components/boxes.py:90` — background_opacity and icon_opacity disagree with the value ColoredBox actually renders

`background_opacity` computes `round((BASE_OPACITY + PER_LEVEL * self.nesting_level) * 100)` from the parent chain only, while `rendered` (line 133) computes the same expression from `level = max(depth, self.nesting_level)` where `depth` is the ContextVar render counter. Take `outer = ColoredBox(body=ColoredBox(body="x"))`. Reading `outer.body.background_opacity` returns 12 (level 1) because the wrapper nodes built in `rendered` have re-attached the body and severed the chain, but `outer.rendered` writes `backgroundcolor=blue!20` for that same inner box. Any caller or test that reads the public property gets a number the document never uses.

### `src/pytex_components/boxes.py:91` — background_opacity and icon_opacity disagree with the value ColoredBox actually renders

`rendered` (line 132) uses `level = max(depth, self.nesting_level)` where `depth` comes from the `_render_depth` ContextVar, because the wrapper nodes break the parent chain. The public properties `background_opacity` and `icon_opacity` use `self.nesting_level` alone. Render `ColoredBox(body=ColoredBox(body="x"))`: the inner box renders with `bg = 20` (level 2), but reading `inner.background_opacity` outside a render returns 12 (level 1). Any caller or test that uses the property to predict or assert the rendered opacity gets the wrong number.

### `src/pytex_components/pagebreak.py:28` — Conditionalpagebreak/Smartsection emit \needspace without requiring the needspace package

`Conditionalpagebreak` returns `ControlSequence("needspace", ...)` with no `required_packages`, and `Smartsection`/`Smartsubsection` (lines 68 and 83) put `\needspace{...}` into a bare `Raw`. `pytex.packages` does define NEEDSPACE, and `pytex_hsrtreport/document.py` loads it, so the bug is hidden there. Render any non-HSRT document, for example `Document(body=Conditionalpagebreak())`, and the preamble contains no `\usepackage{needspace}`; tectonic aborts the compile pass with `Undefined control sequence \needspace`.

### `src/pytex_components/pagebreak.py:42` — Critical and Smartsection render the body eagerly, losing its package requirements

`Critical` calls `body.rendered` at construction and wraps the string in `Raw`, and `Smartsection`/`Smartsubsection` do the same with `head.rendered`. The node tree therefore contains no child node for the body, so the package collector never sees it. `Document(body=Critical(InfoBox("hi")))` renders the mdframed markup into the body but emits no `\usepackage{mdframed}`, `{xcolor}`, `{fontawesome}`, `{calc}` or `{tikz}`, and the compile pass fails with `Environment mdframed undefined`. The resulting `Raw` also defaults to `allow_replacements=True`, so any `\iffalse{pytex(...)}\fi` text produced by the already-rendered body is eval'd a second time at render time.

### `src/pytex_components/pagebreak.py:72` — Smartsection and Smartsubsection render the heading eagerly, so package requirements are lost

Both factories call `head.rendered` and embed the string in a `Raw` node. A `Raw` reports no package requirements, and the `ControlSequence` node is discarded, so the requirement never reaches the preamble. `Smartsection(FaIcon("check"))` renders `\section{\faIcon{check}}` while the preamble never gets `\usepackage{fontawesome5}`, and the compile pass fails with "Undefined control sequence \faIcon". `Critical` documents this same trap; these two did not, so I added the warning to `Smartsection`.

### `src/pytex_components/voting.py:77` — VotingResults.requires omits tikz although its inner ColoredBox needs it

VotingResults builds ColoredBox/CustomBox inside `.rendered`, so their own `requires` never reach the package collector. The set is therefore copied by hand, but it copies MDFRAMED, XCOLOR, FONTAWESOME, MULTICOL and CALC and drops TIKZ, which ColoredBox.requires lists (boxes.py line 108) with the note that tikz is the mdframed framemethod that rounds the filled background. Build a document whose only component is VotingResults: the preamble gets no `\usepackage{tikz}`, so mdframed cannot use framemethod=tikz and the `roundcorner=5pt` corners of the tally box are square (or mdframed errors), while the identical box built through ColoredBox directly renders correctly.

### `src/pytex_components/watermark.py:26` — The watermark text is escaped for backslash and braces only, so a `%` in the text aborts the compile pass

`_watermark_text` escapes `\`, `{` and `}` and nothing else. The result is spliced into a single-line `\DraftwatermarkOptions{scale=...,text={\begin{tabular}{c}...\end{tabular}},color=...}` (lines 59-64). `DraftWatermark("DRAFT 50%")` puts a live `%` into that line, so TeX comments out the remainder of the line including every closing brace, and the compile pass dies with a runaway-argument / "File ended while scanning use of \DraftwatermarkOptions" error. `#` and `_` fail the same way ("You can't use macro parameter character #" and "Missing $ inserted"). The docstring warns about the backslash only, so a caller has no reason to expect the other five characters to be unsafe.

### `src/pytex_components/wordcount.py:29` — Word-count macros hardcode the directory `Build`, but the default build directory is `build`

`\quickwordcount` runs `texcount ... > Build/words.sum` and then `\input{Build/words.sum}`. `pytex_builder/build.py:158` sets `--build-dir` to `Path("build")` by default. On a case-sensitive filesystem the directory `Build` does not exist, so the shell redirect fails, `Build/words.sum` is never written, and `\input` aborts the compile pass with "File `Build/words.sum' not found". The same happens for any `--build-dir` value the user chooses, because the macro never reads it.

### `src/pytex_hsrtreport/document.py:171` — The preamble is frozen in __post_init__, so a later change to body renders a stale preamble

`__post_init__` assigns `self.preamble = self._build_preamble()` once, and `rendered` uses that stored value. `HSRTReport` is a plain (non-frozen) dataclass, so `doc = HSRTReport(body=Empty); doc.body = Concat(Color.hex("00FF00"), "x")` renders a preamble built from the empty body: no `\definecolor{c00FF00}` and no packages picked up from the new colors, so the compile fails. The same applies to a later change of `geometry_options`, `variant` or `show_footer_logos`. The reassigned preamble is also never passed to `attach`, so its root node keeps `_parent = None` after `Document.__post_init__` attached the old `Empty` preamble.

### `src/pytex_hsrtreport/document.py:183` — discovered_colors never walks the title-page fields, so their colors get no \definecolor

`discovered_colors` walks only `self.body` and `self.user_preamble`, but `_body_parts` builds a `TitlePage` from the separate `title`, `abstract`, `keywords` and `data_lines` fields. Build `HSRTReport(body="text", title="T", abstract=Concat(Color.hex("FF0000"), "red"))`: the title page renders the xcolor name `cFF0000`, `_color_definitions` emits no `\definecolor{cFF0000}{HTML}{FF0000}` into the preamble, and tectonic aborts with `Undefined color 'cFF0000'`. Only the three hyperref colors and the palette are safe, because they are added by hand.

### `src/pytex_hsrtreport/document.py:247` — Package requirements of title-page nodes are never collected

`Document.packages` walks `self.body` and `self.preamble` only (src/pytex/model/document.py:49). The `TitlePage` is built inside `_build_full_body`, which `rendered` calls after `self.ordered_packages()`, so no node passed as `title`, `abstract`, `keywords` or a `data_lines` value contributes a package requirement. Pass a node that requires a package outside `BASE_PACKAGES` (for example an `amsmath` math node as `title`): the render omits `\usepackage{amsmath}` and the compile fails with an undefined control sequence. The bug is masked today only because `BASE_PACKAGES` happens to list every package the current title page uses.

### `src/pytex_hsrtreport/document.py:335` — The SVG conversion inside write_inline_logos writes to ./build/ in the process cwd, not to target_dir

`IncludeImage.resolved_path` returns `Path("build") / f"{stem}-{digest}.pdf"` for an SVG source (`src/pytex/model/image.py:91`), a path relative to the process cwd. `read_bytes()` calls `ensure_converted()`, which runs `dst.parent.mkdir(parents=True)` and inkscape on that cwd-relative path. `_emit` then copies the result into `target_dir/logos/`, but the intermediate PDF stays behind. Call `HSRTReport(variant=Variant.ASTA, ...).write_inline_logos("/tmp/out")` from `/srv/app`: `/srv/app/build/ASTA-<digest>.pdf` appears and is never cleaned up, even though the caller named `/tmp/out`. With a read-only cwd (a container whose workdir is on a read-only rootfs, which is exactly the `pytex_api` deployment shape) the `mkdir` raises `PermissionError` and the whole render fails although `target_dir` is writable. Two API requests that convert the same SVG at the same time also race: process B sees `target.exists()` as true while process A's inkscape is still writing, reads a truncated file, and writes a corrupt PDF into its own `logos/`, so tectonic fails on a file that looks correct on the next run.

### `src/pytex_hsrtreport/document.py:355` — inline_image_block and ordered_packages never walk the title-page fields

`rendered` renders `Environment("document", self._build_full_body())`, but `self.inline_image_block` and `self.ordered_packages()` come from `Document`, which walks only `coerce_tex(self.body)` and `coerce_tex(self.preamble)` (`src/pytex/model/document.py:105` and `:68`). `_body_parts` builds the `TitlePage` from the separate `title`, `abstract`, `keywords` and `data_lines` fields, so nothing in those fields is reachable. Build `HSRTReport(body="text", title="T", data_lines=(TitlePageDataLine("Logo", Logo("ASTA")),))`: the title page renders `\includegraphics{build/ASTA-<digest>.pdf}` because `inline_base64` defaults to True, no `filecontents*` block for `build/ASTA-<digest>.pdf.b64` reaches the preamble, and tectonic aborts with "Unable to load picture or PDF file". The same walk gap drops package requirements: a node in `abstract` that requires a package outside `BASE_PACKAGES` (for example `TABULARX` or `SIUNITX`) gets no `\usepackage`, and the compile fails on an undefined control sequence. This is a different code path from the already-reported `discovered_colors` gap, in inherited `Document` code that `HSRTReport` never overrides.

### `src/pytex_koma/document.py:74` — KomaDocument holds the document-class options in a set, so the option order changes on every run

`__post_init__` unions `document_class_options`, `extra_class_options` and `_class_option_flags()` into a `set`, and `DocumentClass._render_options` (src/pytex/model/document_class.py:13) joins that set in iteration order without sorting. Python randomizes `str` hashing per process, so the order is different every run. Verified across five processes with `KomaDocument(body='x', paper='a4paper', fontsize='11pt', div=12, two_side=True, use_geometry=True, draft=False)`: `[final,DIV=12,usegeometry,twoside,a4paper,11pt]`, `[final,usegeometry,a4paper,twoside,DIV=12,11pt]`, `[a4paper,usegeometry,DIV=12,final,twoside,11pt]`, and two more distinct orders. Two builds of the same input therefore write different `.tex` bytes, which breaks reproducible builds and any golden-file test over the rendered `.tex` file. KOMA-Script also processes class options in order and lets a later option win, so whether `usegeometry` lands before or after `DIV=12` changes which type-area calculation applies.

### `src/pytex_markdown/convert.py:309` — An external image URL is passed to includegraphics and its scheme slashes are collapsed

For `kind == "Image"` with an external destination the converter returns `IncludeImage(dest)` unchanged. `IncludeImage.rendered` emits `self.resolved_path.as_posix()`, and `Path` collapses the duplicate slash. Verified: `IncludeImage('https://example.com/logo.png').rendered` is `\includegraphics{https:/example.com/logo.png}`. tectonic cannot fetch a remote file anyway, so `![logo](https://example.com/logo.png)` fails the compile pass with "file not found", and the mangled single slash makes the error message point at a path the author never wrote. The relative branch two lines below has a five-line comment explaining its choice; the external branch has none.

### `src/pytex_markdown/convert.py:315` — Relative image paths resolve against the process CWD, not the Markdown file

`IncludeImage(str(Path(dest).resolve()))` resolves against the current working directory. `IncludeMarkdown` (src/pytex_markdown/__init__.py:81) reads the file by path but never passes that file's directory down, so the converter cannot resolve relative to the Markdown source. Run `pytex doc.tex.py --build` from the repository root with `IncludeMarkdown("docs/guide.md")` where `guide.md` contains `![logo](img/logo.png)`: the node becomes `\includegraphics{<repo root>/img/logo.png}` instead of `<repo root>/docs/img/logo.png`, and the compile pass fails. Every Markdown renderer resolves such a path relative to the containing file, so a `guide.md` that displays correctly in Obsidian breaks the build.

### `src/pytex_markdown/frontmatter.py:35` — Flow-list parsing splits inside quotes, so a name with a comma becomes two people

`_parse_flow_list` splits the inner text on every comma with no quote awareness. Verified: `_parse_flow_list('["Meier, Hans", "Schmidt, Ada"]')` returns `['"Meier', 'Hans"', '"Schmidt', 'Ada"']` — four items, each carrying a stray `"` because `_strip_quotes` only strips a matched pair. Frontmatter `anwesend: ["Meier, Hans", "Schmidt, Ada"]` therefore prints `Anwesend (4)` on the title page with visible double quotes in the names, and `{{count anwesend}}` returns 4 for two people. This is upstream of the reported comma-counting defect: the list never reaches `_joined` with two elements in the first place.

### `src/pytex_markdown/glyphs.py:189` — Non-Unicode cmap subtables are unioned in, so byte codes count as Unicode coverage

_font_codepoints reduces with _or over every cmap subtable without filtering on the platform ID. A format-0 Macintosh subtable maps byte codes 0-255, not Unicode. If a DIN weight carries a MacRoman subtable with a glyph at byte 0xA5, _din_codepoints reports U+00A5 (¥) as covered. renderable_in_din then returns True, is_special_char returns False, and ¥ goes into prose as a bare character that XeTeX renders as tofu with no MissingGlyphWarning. That is the exact silent failure the module exists to prevent.

### `src/pytex_markdown/protocol/convert.py:123` — Any text run holding {{ loses glyph, arrow and citation handling

ProtocolConverter.inline short-circuits to expand_inline_shortcodes whenever the text holds `{{`, skipping super().inline and so _inline_text/_prose. A line such as `Beitrag 50€ am {{datum}} laut @knuth` escapes only LaTeX specials: the `€` reaches the PDF as raw U+20AC and tofus under DIN with no warning, `->` stays literal, and `@knuth` never becomes \textcite. The same line without `{{datum}}` converts correctly, so the defect depends on an unrelated shortcode being present.

### `src/pytex_markdown/protocol/shortcodes.py:107` — {{time ...}} passes unescaped Markdown text into LaTeX

expand_shortcode calls Timestamp(rest) with the raw shortcode remainder. Timestamp wraps it in Textbf, and Parameter.rendered emits a str unchanged, so no escaping happens. A protocol containing `{{time 18:30 (Raum #3)}}` renders \textbf{18:30 (Raum #3)}; `#` is a LaTeX parameter character outside a macro definition, so the compile pass aborts. A `%` would instead silently comment out the rest of the line. Every other shortcode branch routes through escape_latex.

### `src/pytex_markdown/protocol/shortcodes.py:111` — count prints 0 for an unknown field instead of echoing the shortcode

The `count` branch runs `_lookup(meta, rest.lower())`, and `_lookup` returns `None` for an unknown field; `_as_list(None)` is `[]`, so the branch emits `0`. Verified: `expand_shortcode('count anwesende', {'anwesend': ['a','b']})` renders `'0'`, and `expand_shortcode('count', {})` also renders `'0'`, while `expand_shortcode('unknown thing', {})` correctly renders the escaped `{{unknown thing}}`. The module docstring promises "An unknown shortcode goes back into the text as escaped literal text. You then see the typo in the PDF." A single typo in `{{count anwesende}}` therefore prints an authoritative-looking `0` attendees into a signed meeting protocol, with no warning and nothing visibly wrong in the PDF.

### `src/pytex_markdown/protocol/signatures.py:88` — A scalar unterschriften value silently drops the whole signature block

signature_block_from_meta returns None unless meta['unterschriften'] is a list. The frontmatter parser stores `unterschriften: Sitzungsleitung, Schriftführung` as a plain string, because only the `[a, b]` flow form and the `- item` block form become lists. build_protocol then appends no tail and the protocol compiles without any signature lines and without a warning. Every sibling reader (header._as_list, shortcodes._as_list) accepts the comma-separated scalar form.

### `tests/pytex/commands/test_builtin.py:139` — Cite's keyword is named prenote but the test locks in the postnote position

`Cite("k", prenote="see")` is asserted to render `\cite[see]{k}`. In standard LaTeX a single optional argument to `\cite` is the postnote: it prints after the citation, as in "[1, see]". A prenote requires the two-argument biblatex form `\cite[see][]{k}`. The test therefore certifies as correct a parameter whose name states the opposite of what the LaTeX means. Concrete failure: a user writes `Cite("knuth", prenote="cf.")` expecting "cf. [1]" and gets "[1, cf.]" in the compiled PDF, with no test catching the mismatch. The same file's sibling module confirms the inconsistency — test_new_modules.py:246 asserts `Autocite("k", postnote="S. 5")` renders the identical shape `\autocite[S. 5]{k}`, so two different names map to one rendered position, which also breaks the one-name-for-one-thing rule.

### `tests/pytex/commands/test_builtin_extras.py:58` — test_beginaccsupp_with_options uses an empty option value, so it cannot detect a dropped value

The test builds `BeginAccSupp({"ActualText": ""})` and asserts only that `"ActualText=" in out`. Because the chosen value is the empty string, the assertion is satisfied by the key and the equals sign alone. Concrete failure: if the dict-to-options rendering in `Parameter` regressed to emit keys only and discard every value, this test still passes, while every real call such as `BeginAccSupp({"ActualText": "GmbH"})` would silently render `\BeginAccSupp{ActualText=}` and strip the accessibility text from the PDF. Choosing a non-empty value would make the assertion meaningful.

### `tests/pytex/commands/test_new_modules.py:284` — test_listings_commands certifies an lstlisting rendering that cannot compile

Lines 284-285 build `Lstlisting("code", {"language": "python"})` and assert only that `\begin{lstlisting}[language=python]` appears in the output. The docstring of `Lstlisting` in src/pytex/commands/listings.py:92 states the rule the test ignores: the factory adds no line break, listings reads code from the line AFTER `\begin{lstlisting}`, and it needs `\end{lstlisting}` at the start of a line. The rendered value here is `\begin{lstlisting}[language=python]code\end{lstlisting}` on one line. Concrete failure: that exact string makes tectonic consume the rest of the document verbatim, because listings never sees `\end{lstlisting}` at a line start, and the compile pass dies at end of file. The test reports it as correct. The `\end` delimiter is also never asserted, so a factory that dropped the closing tag entirely would pass too.

### `tests/pytex/commands/test_new_modules.py:390` — test_geometry_commands checks only the Newgeometry command name, never its options

Line 390 asserts `Newgeometry({"margin": "1cm"}).rendered.startswith(r"\newgeometry")`. The options dict is passed but nothing verifies it reaches the output. Concrete failure: if `Parameter(options)` regressed to drop an empty-ish or single-key dict, or the options argument were silently ignored, `Newgeometry({"margin": "1cm"})` renders the bare `\newgeometry`, the test passes, and every page after the call keeps the old margins while the author believes the layout changed. Note the sibling `Geometry` assertion two lines above does check `"top=2cm" in out`, so the omission is inconsistent within the same test.

### `tests/pytex/commands/test_new_modules.py:404` — UseCounter is named after \usecounter but the test locks it to \the<counter>

Line 404 asserts `UseCounter("c").rendered == r"\thec"`, and src/pytex/commands/counters.py returns `Raw(f"\\the{name}")`. `\usecounter` is a real and different LaTeX command: inside a `list` environment definition it binds the counter that `\item` steps. `\thec` merely prints the counter's current value. Concrete failure: a user writes `Newenvironment("mylist", Raw(r"\begin{list}{}{") + UseCounter("enumi") + ...)` expecting `\usecounter{enumi}` and gets `\theenumi`, so the list never advances its counter and every item prints the same number, with no test catching it. The test certifies the mismatch instead of flagging it, and no factory exists for the real `\usecounter`, so the registry key `UseCounter` is taken by the wrong command. This is the same one-name-for-one-thing break as the reported Cite/prenote case.

### `tests/pytex/commands/test_new_modules.py:424` — Ifdefstring, Pretocmd and Apptocmd are called with no assertion at all

Lines 424-426 call `Ifdefstring(r"\foo", "bar", "y", "n")`, `Pretocmd(r"\section", "pre")` and `Apptocmd(r"\section", "post")` and discard the results. The test only proves the calls do not raise. Concrete failure: if `Apptocmd` rendered `\pretocmd{\section}{post}{}{}` (wrong control sequence) or omitted the two mandatory success/failure arguments that etoolbox requires, `test_conditionals_commands` still passes green, and the defect only surfaces as a LaTeX error during a compile pass. The same file asserts `.rendered` for every other factory, so these three are an unintended coverage hole.

### `tests/pytex/commands/test_picture.py:26` — test_put_nested_braces_balanced exercises no nested braces and its assertion passes on empty output

The test name promises nested-brace balancing, but the body passed to `Put` is the plain string "ab", which contains no braces at all. The only assertion is `out.count("{") == out.count("}")`, a counting identity that holds for any balanced string. Concrete failure: if `Put` regressed to return an empty `Concat` (rendered == ""), 0 == 0 and the test still passes. It also passes if `Put` dropped the coordinates and rendered just `{ab}`. The real risk the name implies — a body that itself contains `{`/`}`, for example `Put("0", "0", Bold("x"))` producing `\put(0,0){\textbf{x}}` — is never exercised, so an unbalanced `Raw` prefix in `pytex/commands/picture.py` would go undetected.

### `tests/pytex/helpers/test_sanitize.py:19` — test_existing_specials_still_escaped covers 3 of 11 escape entries and never the backslash-brace interaction it is named to guard

`ESCAPES` (src/pytex/helpers/sanitize.py:27) holds 11 entries, and the module comment above it states the load-bearing invariant: `escape_latex` reads the text one character at a time, so it never re-escapes a brace that a replacement adds. The only assertion here is `escape_latex("100% & _x_") == r"100\% \& \_x\_"`, which contains no backslash and no brace. Rewrite `escape_latex` as the obvious chain of `str.replace` calls in `ESCAPES` order — `\` -> `\textbackslash{}` first, then `{` -> `\{` and `}` -> `\}` — and `escape_latex("a\\b")` returns `a\textbackslash\{\}b`, which renders as literal text instead of a backslash. All four assertions in this file still pass, and grep shows no other test asserts on `pytex.helpers.sanitize.escape_latex` output for `\`, `{`, `}`, `~` or `^`.

### `tests/pytex/helpers/test_with_package.py:9` — test_coerce_package_str never checks package identity, so it hides that `coerce_package` bypasses `DefinePackage`

`coerce_package("foo_test_pkg")` returns `Package(pkg)` built directly (src/pytex/helpers/with_package.py:24), not `DefinePackage(pkg)`. `Package` overrides neither `__eq__` nor `__hash__`, so package sets deduplicate by identity, and src/pytex/packages.py states that a constant is safe to compare by identity. The test asserts only `isinstance(p, Package)` and `p.name == "foo_test_pkg"` — a name no constant uses — so the identity contract is never checked. Concretely: `@with_package("amsmath") def Foo(): ...` gives `AMSMATH in Foo().requires == False`, and because `WithPackage.requires` calls `coerce_package(self.package)` on every access, two reads of the same node return two different `Package` objects. `Document.packages` then holds both that object and `AMSMATH`, and `ordered_packages` appends both (src/pytex/model/document.py:88 dedups only inside `by_name`, not in `out`), so the preamble renders `\usepackage{amsmath}` twice. The sibling test test_with_package_wraps_result passes the `AMSMATH` object rather than the string, so the documented string form of `package` has zero identity coverage.

### `tests/pytex/interface/test_tex.py:93` — test_tikz_node_str_label_no_attach asserts on the wrong object and is tautological

The test name claims it proves that a str label gets no parent, but it asserts `n.parent is None` — the parent of the TikZ node itself, not of the label. A freshly constructed detached node always has `parent is None`, so the assert holds no matter what `Node.__post_init__` does. Concretely: change `attach(self, self.label)` in src/pytex_tikz/tikz.py to attach the node to itself, to attach a wrong parent, or delete the call entirely, and this test still passes. It can never fail for the reason its name states, because `attach` already silently skips non-TeX children, so there is nothing observable to assert on a str label in the first place.

### `tests/pytex/interface/test_tex_parent_extras.py:42` — test_coloredbox_parent_str_body_no_attach checks the box's own parent, not the body

Same defect as the TikZ case. `InfoBox("plain string")` is a root node, so `box.parent is None` is true by construction. `ColoredBox.__post_init__` calls `attach(self, self.body, self.icon)`; if that call were changed to attach the box to a wrong parent — for example `attach(self.icon, self)` — the icon-attaching behavior would break while this test still passes green. The test provides zero coverage of the str-body path it is named for.

### `tests/pytex/model/test_color.py:97` — register_named_color mutates global state that no test restores

NAMED_COLORS is a module-level set. test_register_named_color adds "hsrtgray" and test_register_then_named_works adds "hsrtgreen", and neither removes the name afterwards, so the additions persist for the whole pytest session and for every later test module. test_color_named_does_not_register_arbitrary and test_named_unknown_raises depend on a name being absent, so any future test or fixture that registers one of those names first turns them into silent false passes. A fixture that saves and restores NAMED_COLORS is needed.

### `tests/pytex/model/test_color_extras.py:39` — test_overload_three_ints_tuple locks in an int/float dispatch that turns float red into near-black

_from_overload in src/pytex/model/color.py routes a tuple to rgb255 when `all(type(v) is int)` and to rgb when all values are floats. Verified: Color((1, 0, 0)) yields ColorSpec("RGB", "1,0,0"), which is essentially black, while Color((1.0, 0.0, 0.0)) yields ColorSpec("rgb", "1.0,0.0,0.0"), which is red. A user who writes Color((1, 0, 0)) for red in the 0..1 model gets black in the PDF with no error. The mixed case is worse and has no test at all: Color((1, 0.5, 0)) raises TypeError("cannot construct Color from (1, 0.5, 0)"), so writing orange in the float model with an integral 1 and 0 crashes the render. test_overload_three_ints_tuple and test_color.py:66 assert the split is correct, which freezes the trap in place.

### `tests/pytex/model/test_document_extras.py:30` — test_inline_images_excludes_non_inline passes for the wrong reason

The inline and the non-inline IncludeImage share the same path p, and Document.inline_images dedupes by resolved path. If the inline_base64 filter in collect_inline_images were dropped, both nodes would still collapse to one entry and `len(doc.inline_images) == 1` would still hold. The regression the test name promises to catch would ship undetected. Two distinct pdf paths are needed.

### `tests/pytex/model/test_image.py:31` — test_collect_inline_images_filters passes even if the inline filter is removed

Both IncludeImage nodes point at the same pdf_file, and collect_inline_images dedupes by resolved path while keeping the first node it meets. Delete the `and node.inline_base64` condition in src/pytex/model/image.py and the walk still stores only `a` under that one path key, so `found == (a,)` still holds and the test stays green. The test proves dedupe, not filtering. It needs two different paths, one inline and one not.

### `tests/pytex/model/test_image_svg.py:85` — SVG tests write into the repository ./build directory and never clean it up

IncludeImage.resolved_path returns the relative Path("build")/<stem>-<sha1>.pdf, so it resolves against the pytest process working directory, not tmp_path. test_ensure_converted_skips_if_target_exists creates build/x-<sha1 of "<svg></svg>">.pdf in the repo root and never removes it, and test_ensure_converted_invokes_inkscape only unlinks its own target on the success path, so a failed assert at line 80 or 81 leaks build/x-<digest>.pdf. Running the suite from a read-only or a different working directory also changes where these files land, which makes the two tests position-dependent.

### `tests/pytex/model/test_image_svg.py:85` — test_ensure_converted_skips_if_target_exists can mask a real conversion failure in later runs

The test seeds build/x-<digest>.pdf with b"%PDF-already" and leaves it on disk. Any later test or manual build that uses an SVG whose bytes are exactly "<svg></svg>" and whose stem is x will find the stale seeded file, skip inkscape, and embed the 12-byte fake PDF instead of a real conversion. The stale file survives across pytest sessions because nothing deletes it.

### `tests/pytex/model/test_raw.py:48` — test_eval_unterminated_leaves_content_unchanged asserts that a broken marker vanishes without a warning

Raw.rendered returns the content unchanged when PATTERN does not match, and _nested_inner caps nesting at depth 8. The docstring of _nested_inner already admits "the marker stays in the rendered `.tex` file". Because \iffalse ... \fi is a skipped block, a malformed marker such as \iffalse{ pytex(Frac(1,2) }\fi (one missing paren) renders unchanged, LaTeX skips the whole block, the value disappears from the PDF and the build exits 0. The user gets a silently incomplete document. This test asserts that silent pass-through is the correct behavior, so nothing in the suite would notice if a warning were the right answer, and nothing covers the depth-8 cutoff either.

### `tests/pytex/test_registry.py:88` — The duplicate-key assertion is a hard-coded negative substring and can go vacuous

The test proves absence by checking that a literal message is not in stderr. Two ways it silently stops testing anything: (1) reword the warning in `Registry.add` (src/pytex/registry.py) from "Duplicate key in registry (overwritten): {key}" to anything else, and the assert passes even when the Fill key collides again — the regression it guards returns undetected. (2) `Registry.add` uses `Logger(cls.__name__)` rather than `logging.getLogger`, so the record only reaches stderr via logging's lastResort handler. Any future call to `logging.basicConfig`, `logging.disable`, or a `logging.lastResort = None` at import time of `pytex` routes the warning away from stderr, and the test becomes permanently vacuous.

### `tests/pytex/test_template.py:41` — test_list_interpolation_maps_each_element uses only TeX nodes, so the escape branch for list items is untested

The test interpolates `[Bold('a'), Bold('b')]`. In `_coerce` (src/pytex/template.py:96) the list branch calls `_coerce(item)` per item, but for a TeX item that recursion returns the node unchanged — the same result the `isinstance(value, TeX)` branch gives. Change line 98 from `Concat(*(_coerce(item) for item in items))` to `Concat(*items)` and every template test still passes, because `Concat` coerces a plain `str` through `coerce_tex` into an unescaped `Raw` with `allow_replacements=True`. Then `tex(t"{['50% off']}")` renders `50% off`, where `%` starts a LaTeX comment and eats the rest of the line, and an item containing `\iffalse{pytex(...)}\fi` executes as Python at render time. No test in the file interpolates a list of plain strings, so this escape boundary is unguarded.

### `tests/pytex_analyze/test_analyze.py:33` — Undefined-cref assertion matches the bare letter b anywhere in a message

`assert [i.message for i in issues if "b" in i.message]` accepts any issue whose message contains the letter b. A message such as "label 'a' is defined but never used" satisfies it. If `Cref` stopped splitting its comma-separated labels and only ever checked the first one, the test could still pass on an unrelated issue, so it does not prove that label b was checked.

### `tests/pytex_api/test_compile.py:37` — The shell-escape assertions test exact list membership, so a differently spelled flag slips through

`assert "shell-escape" not in cmd` on a `list[str]` is an exact-element test, and it only passes today because `build_tectonic_cmd` happens to emit the two-token form `["-Z", "shell-escape"]`. Concrete failure: change `build_tectonic_cmd` to the equally valid single-token form `cmd.append("-Zshell-escape")`, or to tectonic's `--shell-escape`, and drop the `if policy.allow_shell_escape` guard by mistake. Both `test_untrusted_cmd_forces_no_shell_escape_and_only_cached` and `test_sandboxed_cmd_forces_no_shell_escape_and_only_cached` still pass, while every untrusted build now runs with shell-escape enabled. The check should be `assert not any("shell-escape" in a for a in cmd)`. Both test names also claim the argv 'forces no shell escape', but no explicit disable flag is ever emitted; the safety rests on tectonic's default.

### `tests/pytex_api/test_render_blob.py:228` — The temp-path leak check hardcodes "/tmp" instead of the real temporary directory

`_expect_clean_compile_error` asserts `"/tmp" not in msg` to prove a CompileError leaks no temporary work directory. The path is never derived from the directory actually used. Concrete failure: run the suite on macOS, or with `TMPDIR=/var/tmp` or `pytest --basetemp=/home/ci/work` set in CI. A regression that embeds the full temporary work directory in the error message (for example an unwrapped `SyntaxError` whose filename is `/var/folders/xy/.../input.py`) produces a message with no `/tmp` substring, so all four `test_*_becomes_compile_error` tests pass while the API leaks host paths to remote callers. The assertion should compare against `tempfile.gettempdir()` or the actual work directory.

### `tests/pytex_api/test_sandbox.py:248` — test_should_sandbox_true_for_host_binary_without_image locks in a wrong claim: the image is still required

The test asserts `_should_sandbox(...) is True` for `SandboxConfig(tectonic_in_image=False)` when `sandbox_image_present` returns False, and `_should_sandbox` in src/pytex_api/_compile.py:224 short-circuits the image check for that config. But `build_podman_cmd` (src/pytex_api/_sandbox.py:509) unconditionally appends `config.image` to the argv; mounting a host binary at `CONTAINER_BINARY` does not remove the need for a container image. Concrete failure: configure `tectonic_in_image=False` on a host that has podman but has never run `pytex-sandbox-init`, then submit an untrusted PDF build. `_should_sandbox` returns True, so the fail-closed branch at _compile.py:328 is skipped, `podman run --network none ... pytex-sandbox:latest` cannot resolve the missing image, and the request dies with a raw podman 'image not known' error instead of the clear 'the OS sandbox is required ... refusing to downgrade' CompileError. If a deployment ever relaxes `--network none`, the same path would pull an image from a registry at request time, which `_should_sandbox`'s own docstring says must never happen.

### `tests/pytex_builder/test_render.py:64` — _force_py313 mutates the real sys module for the whole test

`monkeypatch.setattr(render_mod.sys, "version_info", (3, 13, 0, "final", 0))` patches the attribute on the global `sys` module object, not on a module-local alias, so every piece of code running inside that test sees Python 3.13. On the 3.14 interpreter in the dev shell, any lazily imported library or pytest plugin that branches on `sys.version_info` during `_render_python` (for example a `if sys.version_info < (3, 14): raise RuntimeError(...)` guard) takes the wrong branch, and the resulting error surfaces as an unrelated BuildError. Patching `render_mod._import_error_message`'s inputs, or a module-level constant, would be contained.

### `tests/pytex_builder/test_render.py:107` — Dead assertion: the substring "needs\nPython 3.14" can never occur

`_import_error_message` in src/pytex_builder/render.py builds the hint as `'... which needs ' + f"Python 3.14; you are on Python {major}.{minor}"`, so the text is "which needs Python 3.14" with a space, never a newline. `assert "needs\nPython 3.14" not in str(exc.value)` therefore passes unconditionally. If a regression made the hint fire on Python 3.14 or later, this assertion would not catch it; only the second assertion ("you are on Python") has any effect. The test is also skipped on the CI interpreter (<3.14), so nobody notices.

### `tests/pytex_builder/test_render.py:126` — test_get_tex_node_does_not_render never checks that no render happened

The body is `node = get_tex_node(src)` followed by `assert node.rendered == r"\emph{x}"`, which is exactly what test_tex_input_is_wrapped_and_rendered already checks through render_input. Nothing observes whether get_tex_node rendered eagerly. Change `get_tex_node` to `return Raw(IncludeTeX(path).rendered)` for the `.tex` branch and the test still passes, yet `--tree` (pytex_builder/tree.py walks the node returned by get_tex_node) would then print a single `Raw` line instead of the node tree, and the optimize pass would receive an already-flattened node. A real assertion would inspect `type(node)` / the child nodes, or use a node whose `.rendered` has a side effect counter.

### `tests/pytex_builder/test_tectonic.py:193` — test_extract_biber_from_tar_picks_largest_biber never exercises the largest-member rule

The tar holds `._biber` (4 bytes) and `biber` (10 bytes), but `_is_biber_member` already rejects any name starting with `._`, so exactly one candidate reaches `max(tar_members, key=lambda m: m.size)`. Replace that `max(...)` with `tar_members[0]` in src/pytex_builder/tectonic.py and the test still passes. A real musl tarball that ships both `biber` (a small wrapper) and `biber-linux_x86_64-musl` (the real binary) would regress undetected.

### `tests/pytex_builder/test_tectonic.py:295` — No test covers a system biber of the wrong version

testbiber_for_build_matches_system_biber is the only test that puts a biber on PATH, and it makes `biber --version` report exactly the version the BCF file asks for, so the guard `if f"biber version: {biber_ver}" in result.stdout` (src/pytex_builder/tectonic.py:478) is only ever exercised on the true branch. Delete that `if` and return `Path(system_biber)` unconditionally and the whole suite still passes. On a machine with TeX Live 2021 (biber 2.16) building a document whose `.bcf` is version 3.12, PyTeX would hand tectonic the 2.16 binary instead of downloading 2.21, and the build dies with "Found biblatex control file version 3.12, expected version 3.5" instead of silently downloading the right biber.

### `tests/pytex_builder/test_tectonic.py:340` — test_run_makeindex_success_returns_true only asserts argv[0]

run_makeindex builds `[makeindex, "-s", style.name, "-t", log, "-o", output, source]` with `cwd=build_dir` (src/pytex_builder/tectonic.py:598). The test captures the whole cmd list in `calls` but asserts only `calls[0][0] == "/usr/bin/makeindex"`. Swap `-t` and `-o`, drop `-s style.name`, or drop `cwd=build_dir`, and the test stays green. In a real build the `-o`/`-t` swap writes the makeindex log to `job.gls`, so tectonic's next compile pass reads the log as the glossary and the PDF ships a glossary full of makeindex diagnostics; dropping `-s` makes glossaries render with the wrong style.

### `tests/pytex_components/test_voting.py:21` — test_renders_with_picked_color cannot fail on a wrong picked color

`VotingResults.rendered` (src/pytex_components/voting.py:90-106) hardcodes the three per-column boxes as "britishracinggreen" (Ja), "red" (Nein) and "eggplant" (Enthaltung). Every rendered tally therefore contains all three color names, whatever `self.color` is. Failure scenario: swap the branches in `_vote_color` so `yes > no` returns "red"; the box background and the vote-yea icon of a passed motion turn red, and `assert "britishracinggreen" in out` still holds, as do "thumbs-up", "thumbs-down" and "vote-yea". Nothing in the file checks that `self.color` reaches `background_color`/`icon_color`, so the only render-level color test in the suite passes for the wrong reason. `test_color_picked_in_python` covers the selection function alone.

### `tests/pytex_components/test_voting.py:31` — Vote-count assertion is nearly tautological

`assert "7" in out and "2" in out and "1" in out` checks single digits against the whole rendered LaTeX. The colored box already renders `blue!12`-style opacity values, so `"1"` and `"2"` are present regardless of the counts. If `VotingResults` rendered abstain=1 as 0, or swapped no and abstain, the test would still pass.

### `tests/pytex_hsrtreport/test_titlepage_voting.py:100` — test_voting_displays_count_strings passes for the wrong reason: "3" comes from \begin{multicols}{3}

VotingResults.rendered always wraps the three tallies in Multicols(3, ...), which renders the literal substring `\begin{multicols}{3}`. The test calls VotingResults(yes=42, no=7, abstain=3) and asserts `"3" in out`. If a regression dropped the abstain CustomBox entirely, or rendered the wrong abstain value, the assertion still succeeds because the multicols column count supplies a "3". Pick an abstain value that cannot appear elsewhere (for example 91) or assert on the full `\textbf{Enthaltung:} 3` fragment.

### `tests/pytex_koma/test_commands.py:122` — test_head_foot_commands_attach_pkg checks only `requires`, so five of the six head/foot factories have no rendering test

`src/pytex_koma/commands.py` defines Ihead, Chead, Ohead, Ifoot, Cfoot and Ofoot as six near-identical one-line factories that each pass a hand-written macro name string to `_scoped_head_foot`. The loop at line 123 asserts only `SCRLAYER_SCRPAGE in out.requires`, and `test_ihead_with_scope` is the single test that pins a rendered macro (`\ihead[L]{text}`). A grep over tests/ and src/ finds no other use of Chead, Ohead, Ifoot, Cfoot or Ofoot. If a copy-paste edit made `Ofoot` return `_scoped_head_foot("cfoot", ...)`, `Ofoot("Seite 1").rendered` would be `\cfoot{Seite 1}`, the footer text would move from the outer corner to the center of every page, and the whole suite would stay green. Add an assertion on the rendered macro name inside the existing loop.

### `tests/pytex_markdown/test_citations.py:62` — `test_email_is_not_a_narrative_citation` never reaches the citation regex it claims to guard

The test exists to pin the `(?<![\w@])` lookbehind in CITATION_RE (convert.py:124), which stops `foo@bar` from reading as a narrative citation. It never exercises it. I ran `Markdown('write to a@b.com today').rendered` and got `'write to \\href{mailto:a@b.com}{a@b.com} today'` — marko's gfm autolink extension turns the address into a Url node, so `_inline_text` gets no text containing `@`. Concrete: remove `(?<![\w@])` from convert.py:124 and this test still passes, but an address without a TLD is not autolinked and goes through `_inline_text`. I verified with the modified pattern that `'see foo@bar here'` then matches `@bar`, so the prose renders `see foo\textcite{bar} here` and a bogus `\textcite` reaches the rendered `.tex` file. A meeting protocol that writes `schriftfuehrung@stupa` in prose loses the text and gets an undefined citation key.

### `tests/pytex_markdown/test_eval_comment.py:19` — The only non-eval link-ref-def test differs in both gated fields, so neither half of the code-execution gate is pinned

convert.py:483-488 evaluates a `LinkRefDef` only when `label == "//"` AND `dest == "#"`. `test_non_comment_link_ref_def_renders_nothing` feeds `[ref]: https://example.com "title"`, which fails BOTH conditions, so it cannot tell which condition is load-bearing. No other test in the repo (I grepped `LinkRefDef` and `[//]` across tests/ and src/) supplies a label-only or dest-only mismatch. Concrete: delete `getattr(node, "label", None) == "//"` from convert.py:484 and the whole suite stays green. I confirmed with marko that `[ref]: # "1+2"` parses to LinkRefDef(label='ref', dest='#', title='"1+2"'), so after that edit `[ref]: # "__import__('os').system('id')"` executes Python during conversion. The defense-in-depth stripper for non-trusted builds does not cover it either: `_EVAL_COMMENT_RE` in src/pytex_api/_security.py:51 is `^[ \t]*\[//\]:[ \t]*#.*$` and matches the `//` label only.

### `tests/pytex_markdown/test_frontmatter.py:73` — Keep-chomping test asserts one newline fewer than YAML produces

The block scalar in `b: |+` holds the content line 'line1' and two blank lines. Per YAML 1.2 (chomping example 8.5) every line contributes its own line break, so `|+` keeps 'line1\n\n\n'. `_render_block` in src/pytex_markdown/frontmatter.py joins the dedented lines with `"\n".join(...)`, which drops the terminator of the last line and gives 'line1\n\n'. The test asserts that value, so it locks the deviation in. A frontmatter value written with `|+`, for example a `bibliography` block, reaches LaTeX with one trailing newline fewer than any real YAML parser gives, and a later switch to PyYAML changes the rendered `.tex` file.

### `tests/pytex_markdown/test_functional_equivalence.py:150` — The `_prose` reference is not independent and covers only the euro path

`_old_prose` (line 80) calls the new `_escape_text`, not `_old_escape_text`, so a regression inside `_escape_text` changes both sides of the comparison and the test still passes. `_old_prose` also splits on the euro sign only, while the new `_prose` routes every entry of `GLYPH_NODES` and every unrenderable character through `glyph_node`. PROSE_SAMPLES (line 47) holds no `→ ↔ ≤ ≥ ·` and no unrenderable character, so that path is unpinned. Concrete failure: add 'a → b' to PROSE_SAMPLES and `test_prose_matches_reference` fails while `_prose` is correct, because `_old_prose` leaves the raw `→` in the output. PROSE_SAMPLES is shared with `test_escape_text_matches_reference`, so widening one test breaks the other.

### `tests/pytex_markdown/test_unicode_glyphs.py:49` — Unicode/ASCII arrow parity is claimed but only holds for two of eight arrows

`test_arrow_targets_match_ascii_arrows` checks only `→` and `↔`, so it reads as proof that the Unicode and ASCII arrow spellings agree. `GLYPH_NODES` in src/pytex_markdown/glyphs.py has entries for `→` and `↔` only, while `ARROWS` in convert.py has eight ASCII arrows. I confirmed the gap: `Markdown('a ← b').rendered` returns 'a \texttt{[missing glyph]} b', and `Markdown('a ⇒ b').rendered` does the same, while 'a <- b' and 'a => b' render `$\leftarrow$` and `$\Rightarrow$`. A document that uses `←`, `⇒`, `⇔`, `⟶`, `⟵`, or `⟷` loses the character in the PDF.

### `tests/pytex_markdown/test_unicode_glyphs.py:80` — `test_renderable_char_left_as_text` covers only German diacritics and hides a 107-code-point hole in the DIN coverage rule

`_din_codepoints` (src/pytex_markdown/glyphs.py:153) intersects the cmaps of all six bundled DIN weights, so a character present in some weights but not all counts as unrenderable and `is_special_char` routes it to `[missing glyph]`. I measured the gap: the union over the weights is 335 code points, the intersection is 228, so 107 code points fall into the hole, including all of Latin Extended-A. The test only checks `Grüße über Lösungen`, and umlauts are in every weight, so it passes while the hole stays invisible. Concrete: I ran `Markdown('Karel Čapek').rendered` and got `'Karel \\texttt{[missing glyph]}apek'`, and `Markdown('Łódź').rendered` gave `'\\texttt{[missing glyph]}ód\\texttt{[missing glyph]}'`. A `gaeste` or `anwesend` entry with a Czech or Polish name loses characters in the meeting protocol PDF, and no test fails.

### `tests/pytex_protocol/test_render.py:29` — Tally assertion passes on substrings of unrelated output

`assert "12" in out and "3" in out and "2" in out` is satisfied almost entirely by other text. `"2" in out` is implied by `"12" in out`, and `"3"` appears in the rendered opacity values (level 1 gives background 12 and icon 32). If the converter parsed only the Ja count and dropped Nein: 3 and Enthaltung: 2 from the `VotingResults` box, this test would still pass.

### `tests/pytex_protocol/test_render.py:46` — Inline-shortcode test is satisfied by the unexpanded literal

`test_inline_shortcode_in_paragraph` renders "Beginn um {{time 9:00}}." and asserts only `"9:00" in out`. When a shortcode is not expanded, the converter escapes the text and emits `Beginn um \{\{time 9:00\}\}.`, which still contains "9:00". Failure scenario: break the `"{{" in text` guard in `ProtocolConverter.inline` (src/pytex_markdown/protocol/convert.py) or make `inline` fall through to `super().inline`; no paragraph shortcode is expanded any more, every meeting protocol ships with literal braces in the PDF, and this test stays green. The sibling `test_field_reference_uses_meta` would catch it only because "AStA" comes from the metadata, not from the source text.

### `tests/pytex_protocol/test_shim.py:13` — Re-export test passes vacuously when __all__ is empty

`test_pytex_protocol_reexports_public_api` loops over `new.__all__` and asserts inside the loop only. If `pytex_markdown.protocol.__all__` were emptied or renamed (for example during a refactor that moves the public names elsewhere), the loop body never runs and the test reports success while the deprecation shim re-exports nothing at all.

### `tests/pytex_protocol/test_shim.py:29` — importlib.reload of pytex_protocol mutates interpreter-wide state

`test_pytex_protocol_import_warns` reloads `pytex_protocol` in place. The reload rebinds every attribute of the already-imported module object for the rest of the pytest session. Any later test in another file that holds a reference taken before the reload, or that asserts object identity against the shim, can see a stale object and fail depending on collection order. The test also does not restore the pre-reload module, so the leak is permanent for the session.

## Severity low

### `examples/document.tex.py:3` — Docstring claimed the render output lands in the working directory, not the build directory

The old usage line read `pytex examples/document.tex.py  # -> document.out.tex`. `_default_output` in src/pytex_builder/build.py returns `build_dir / f"{_slug(base.name)}.out.tex"` and `--build-dir` defaults to `Path("build")`, so the real path is `build/document.out.tex`. A reader who runs the command and then looks for `document.out.tex` in the repository root finds nothing. I corrected the docstring; no code change.

### `examples/hsrtreport.tex.py:156` — Rendered demo text uses the British spelling "colour"

The literal `"A custom box with a chosen icon and colour."` prints "colour" in the demo PDF, while the house style and the code both use the American form (the module is `pytex_hsrtreport/colors.py`, the parameter is `color`). The same literal also appears in examples/hsrtreport-tstrings.tex.py line 147, and examples/templatestring.tex.py renders "emphasised" the same way. String literals are out of scope for this pass, so I left all of them byte-identical.

### `examples/hsrtreport.tex.py:203` — Comment claimed a `\par` before and after Keeptogether, but only the one after exists

The old comment said "\par before and after keeps it in vertical mode", while the code has `Keeptogether(...)` followed by a single `Raw(r"\par")` and nothing before it. Here the preceding `Subsection("Page-break helpers")` happens to leave LaTeX in vertical mode, so the output is correct by accident. Anyone who copies this block into running prose, following the comment, gets the `\linewidth` minipage glued to the end of the previous paragraph and an overfull hbox. I rewrote the comment to describe only the `\par` that is there; the code is unchanged.

### `packaging/build.py:33` — The build installs into sys.executable and fails on an externally managed interpreter

`main()` runs `[sys.executable, "-m", "pip", "install", "pyinstaller", *requirements]` against whatever interpreter started the script. On a Debian, Fedora or Nix system Python (PEP 668), pip exits 1 with "error: externally-managed-environment", `check=True` raises CalledProcessError, and the traceback does not tell the user that a virtualenv was needed. The docstring warns to use a fresh virtualenv, but the script neither checks `sys.prefix != sys.base_prefix` nor prints a hint on failure.

### `packaging/build.py:41` — build.py always prints "Built dist/pytex", but on Windows PyInstaller writes dist/pytex.exe

NEW. `main()` ends with `print("\nBuilt dist/pytex")` regardless of the platform. On Windows PyInstaller writes `dist/pytex.exe`, which .github/workflows/release.yml encodes in the matrix as `bin: dist/pytex.exe`. A Windows developer who follows the printed path runs `./dist/pytex --version` and gets a file-not-found error. The packaging/README.md build block has the same Linux-only path, but it is inside a `sh` example, so it is in scope for the shell it names.

### `packaging/pytex.spec:22` — `_PYTEX_PACKAGES` omits `pytex_components`, so it is bundled only by accident

CONFIRMED. src/ holds ten packages. `_PYTEX_PACKAGES` (lines 22-31) lists eight and leaves out `pytex_components` and `pytex_api`. `pytex_api` is plausibly deliberate (server only, extra deps). `pytex_components` is a documented public package (README.md line 215 table row) that a `.tex.py` file may import directly. It reaches the binary only because src/pytex_hsrtreport/__init__.py line 6 statically imports it, including the submodule names `boxes`, `citations`, `cleveref_names`, `pagebreak`, `voting`, `watermark`, so PyInstaller's Analysis follows the chain. `collect_all` never runs on it. If that compatibility re-export is dropped or trimmed, `from pytex_components.voting import VotingResults` fails in the frozen binary with ModuleNotFoundError while the same document works under a pip install.

### `src/pytex/commands/builtin.py:351` — Itemize and Enumerate with no items render an empty environment that LaTeX rejects

`Concat()` with no surviving child returns `Empty`, so `Itemize()` renders `\begin{itemize}\end{itemize}`. Verified render. LaTeX aborts the compile pass with "Something's wrong--perhaps a missing \item". The realistic trigger is a comprehension: `Itemize(*[Item(t) for t in tags if t.visible])` with no visible tag breaks the whole build instead of rendering nothing. `Description` has the same shape at line 378.

### `src/pytex/commands/builtin.py:378` — Description passes a bare string straight through, producing a description body with no \item

_describe_item returns any non-tuple unchanged, including a str. Description("hello") renders \begin{description}hello\end{description}, and LaTeX aborts with "Something's wrong--perhaps a missing \item". Itemize and Enumerate wrap a bare str in Item() for exactly this reason, so the three list factories behave inconsistently for the same input.

### `src/pytex/commands/builtin.py:490` — IncludeOnly with no paths renders \includeonly{}, which silently drops every included file

`IncludeOnly(*paths)` joins the paths with a comma and always emits the required argument. Verified: `IncludeOnly().rendered` is `\includeonly{}`. That is valid LaTeX with the meaning "include nothing", so LaTeX raises no error at all. A caller that builds the list by filtering, for example `IncludeOnly(*[c for c in chapters if c in selected])`, and whose filter matches nothing, gets a PDF with the title page and an empty body, no warning from LaTeX, and no diagnostic from PyTeX. Returning `Empty` for zero paths would make the empty case mean "no restriction", which is what a caller building a filtered list expects.

### `src/pytex/commands/builtin.py:580` — Verbatiminput declares no package requirement, and packages.py has no verbatim entry to point at

`\verbatiminput` is defined by the `verbatim` package, not by the LaTeX kernel. `Verbatiminput` carries no `@with_package`. Verified: `Verbatiminput('notes.txt').requires` is `frozenset()`. A document that includes a source file with `Verbatiminput` gets no `\usepackage{verbatim}` and the compile pass fails with "Undefined control sequence \verbatiminput". This one needs two changes rather than one: `packages.py` defines no `verbatim` package at all (grep for "verbatim" in that file returns nothing), so the constant has to be added before the decorator can be applied.

### `src/pytex/commands/definitions.py:31` — _cmd silently drops default when nargs is None

The default parameter is only appended inside the `if nargs is not None` block. Newcommand("\\foo", "body", default="x") renders \newcommand{\foo}{body} with no diagnostic, so the caller's default value vanishes. LaTeX does need nargs before a default, so a raised error would be the safe response instead of a silent drop.

### `src/pytex/commands/glossaries.py:38` — Newglossaryentry braces each value but never checks the value for a closing brace, so an unbalanced value breaks the group

The rewritten comment above line 38 explains why each value is braced, and the brace does fix the comma hazard. It does not fix an unbalanced brace in the value. `Newglossaryentry('api', {'description': 'a set of calls, see } for details'})` renders `\newglossaryentry{api}{description={a set of calls, see } for details}}`, where the value's own `}` closes the group early. LaTeX then reads `for details` as a stray key and hits an extra `}`, and the compile pass fails with "Missing } inserted" at a line far from the real cause. The `opts` string is also handed to `Raw`, which defaults to `allow_replacements=True`, so a `\iffalse{pytex(...)}\fi` sequence inside a glossary description is evaluated as Python instead of printed.

### `src/pytex/commands/graphics.py:51` — Includegraphics cannot express a graphicx flag option through extra_options

The extra generator is `(f"{k}={v}" for k, v in (extra_options or {}).items())`, with no bare-key branch - unlike the sibling helpers in fontspec.py:24 and mdframed.py:19, which emit `k` alone when the value is an empty string. Includegraphics("fig.png", extra_options={"clip": ""}) renders `\includegraphics[clip=]{fig.png}`; graphicx defines `clip` as a keyval boolean with default true, so the empty value makes the compile pass stop with "Package keyval Error: clip undefined". The same applies to `draft`, `final` and `noclip`. A caller must pass the redundant `"true"` instead, which is not discoverable from the signature.

### `src/pytex/commands/graphics.py:71` — Graphicspath() with no paths renders \graphicspath{} and breaks image lookup

`inner` is "" when *paths is empty, so the factory renders `\graphicspath{}`. That defines `\Ginput@path` as an empty token list rather than leaving it undefined, and graphicx then searches an empty list of directories instead of falling back to its default lookup. A .tex.py file that computes its image directories and ends up with none - for example `Graphicspath(*cfg.get("image_dirs", []))` - silently disables every later `\includegraphics`, and the compile pass reports "File `fig.png' not found" for images that sit next to the rendered .tex file. Guarding on an empty tuple and returning Empty would avoid it.

### `src/pytex/commands/listings.py:25` — listings _opts_to_str cannot render a flag option

This helper always writes `f"{k}={v}"`, unlike the sibling helpers in fontspec.py:20 and mdframed.py:15, which emit a bare key when the value is an empty string. Lstset({"frame": ""}) renders `\lstset{frame=}`, and listings rejects the empty value for a key that takes no argument, so the compile pass reports a package error instead of setting the flag.

### `src/pytex/commands/listings.py:77` — Lstinline builds broken LaTeX when the code holds the delimiter

Lstinline interpolates the body between two copies of `delim` with no check. Lstinline("a | b") renders `\lstinline|a | b|`, which closes the inline listing after "a " and leaves ` b|` as body text. The default delimiter is a vertical bar, so any shell pipeline, Python union type, or C or-operator in the snippet corrupts the page.

### `src/pytex/helpers/with_package.py:28` — Every @with_package factory returns an unhashable, mutable node while plain factories return frozen hashable ones

`WithPackage` is a plain `@dataclass`, so Python generates `__eq__` and sets `__hash__` to None. `ControlSequence` is `@dataclass(frozen=True, slots=True)` and stays hashable. Verified: `hash(Toprule())` raises "TypeError: unhashable type: 'WithPackage'" while `hash(Hline())` returns an integer. Any code that de-duplicates nodes through a set, or keys a memo dict by node — a cache in the optimize pass, or user code doing `set(collected_nodes)` — works for kernel commands and crashes for every package-carrying node (`Toprule`, `Euro`, `Gls`, all of biblatex). `WithPackage` is also the only mutable node type, which contradicts the immutability that the TeX node contract states.

### `src/pytex/model/color.py:103` — Color error messages use British "colour" while the whole public API uses "color"

Color.hex raises "invalid hex colour: ..." and Color.named raises "unknown colour name ...; register via register_named_color". Every identifier in the module is American (Color, collect_colors, register_named_color, NAMED_COLORS). A user who greps the source or the docs for the phrase "unknown color name" after seeing the traceback finds nothing. The named() message also contains a semicolon, which the house style bans in prose.

### `src/pytex/model/color.py:125` — Color.rgb derives the name from the rounded 0-255 triple, so two near colors collide and only the first gets a \definecolor

The name is `f"crgb{int(r * 255):03d}..."` while the spec keeps the exact floats. Two colors within 1/255 of each other therefore share a name but differ in spec. Verified: `Color.rgb(0.5,0.0,0.0)` and `Color.rgb(0.501,0.0,0.0)` both get the name `crgb127000000`, and `a == b` is False. `collect_colors` keys `seen` on `node.name`, so `collect_colors(Concat(a, b))` returns only `('crgb127000000', ColorSpec(model='rgb', value='0.5,0.0,0.0'))`. The second color node renders the name `crgb127000000`, which resolves to the first color's definition. The document prints the wrong shade with no error.

### `src/pytex/model/color.py:209` — _from_overload rejects a mixed int/float rgb tuple instead of reading it as a float triple

The dispatch is `all(type(v) is int ...)` then `all(isinstance(v, float) ...)`. A tuple that mixes the two satisfies neither branch and falls through to the TypeError at line 217. Verified: `Color((1, 0.0, 0.0))` raises `TypeError: cannot construct Color from (1, 0.0, 0.0)`. Writing pure red as `Color((1, 0.0, 0.0))` is the obvious form once a reader has seen the documented `Color((1.0, 0.0, 0.0))` overload, and any computed triple such as `(0, 0.5, 1)` hits the same path. The error message names no accepted form, so the caller has to read the source to learn that every component must carry the same Python type.

### `src/pytex/model/document.py:56` — get_packages walks the node tree with no visited set, so a shared subtree costs exponential time

`get_packages` recurses into `obj.children` unconditionally, and `Concat` keeps a repeated child rather than deduplicating it. A node tree that is a DAG is therefore expanded as if it were a tree. Measured in this worktree: `n = Raw('x')` doubled 19 times with `n = Concat(n, n)` makes `Document(body=n).packages` take 1.38 seconds for a result of at most a handful of packages. Twenty-five doublings take minutes and thirty take about an hour, with no output and no progress. `collect_colors` and `collect_inline_images` share the defect, and `Document.rendered` touches all three. A document that builds a shared block once and reuses it through several nesting levels hangs the render step for no visible reason.

### `src/pytex/model/image.py:74` — resolved_path re-reads and re-hashes the whole SVG on every access

`resolved_path` calls `hashlib.sha1(src.read_bytes())` with no caching, and `rendered`, `ensure_converted`, `read_bytes`, `collect_inline_images` and `Document.inline_images` all touch it. A single `Document.rendered` for a document with one 5 MB SVG reads and hashes that file six or more times. It also means `rendered` raises FileNotFoundError for a missing SVG, while a missing PNG renders fine and only fails later in the compile pass.

### `src/pytex/model/image.py:90` — hashlib.sha1 without usedforsecurity=False breaks resolved_path on a FIPS host

`resolved_path` calls `hashlib.sha1(src.read_bytes())` for content addressing, not for security. On a host whose OpenSSL runs in FIPS mode — a RHEL or UBI CI image with FIPS enabled, which is common for institutional infrastructure — the constructor raises `ValueError: [digital envelope routines] unsupported`. Every SVG document then fails at render time, before the compile pass starts, with an error that names a hash algorithm and not the image. Passing `usedforsecurity=False` states the intent and keeps the call legal. The result depends on the host, not on the input.

### `src/pytex/model/raw.py:47` — Deeply nested pytex(...) markers silently pass through unreplaced

`_nested_inner(8)` builds a regex that matches at most eight levels of nested parentheses. An expression such as `pytex(Concat(Bold(Frac(Sum(Int(Sqrt(Text(Mathbb("x")))))))))` exceeds that depth, so `PATTERN` does not match. `Raw.rendered` returns the content unchanged and the literal `\iffalse{pytex(...)}\fi` reaches the rendered `.tex` file. There is no warning and no error, so the marker is simply missing from the PDF.

### `src/pytex/packages.py:24` — FONTENC carries no encoding option, so it renders a no-op `\usepackage{fontenc}`

`DefinePackage("fontenc")` has an empty `options` set, and `Package.rendered` emits `\usepackage{fontenc}` with no bracket group. fontenc selects an encoding only from its option list; with none it loads and changes nothing, so the engine default stays in force. A node that names `packages.FONTENC` as its package requirement in order to get T1 therefore gets no encoding change at all, and the `\textbackslash{}`, `\textasciitilde{}`, `\textasciicircum{}` and `\textquotedbl{}` macros that `escape_latex` emits are left depending on whatever encoding the engine happens to default to. `DefinePackage` also ignores `options` for a name that already exists, so a later `DefinePackage("fontenc", options={"T1"})` in a downstream package silently returns this optionless instance and drops the T1 request without a warning. `FONTENC` is reachable both as a module constant and as `Packages.FONTENC`.

### `src/pytex/registry.py:47` — Registry.add builds a Logger directly instead of calling logging.getLogger

Logger(cls.__name__) constructs an orphan Logger whose `parent` is None and which the logging manager does not know about. An application that calls logging.basicConfig or configures handlers on the root logger never receives the duplicate-key warning; it falls through to logging.lastResort on stderr instead, and it cannot be filtered, formatted, or silenced by normal logging configuration. A duplicate registry key therefore overwrites an existing factory with a warning the host application cannot capture.

### `src/pytex/template.py:94` — The list/tuple branch in _coerce runs before the conversion is applied

_coerce tests isinstance(value, (list, tuple)) before it looks at `conversion`, so `tex(t"{[1, 2]!r}")` concatenates the escaped items and renders "12" instead of the requested repr "[1, 2]". The `value is None` branch on line 86 has the same effect: `tex(t"{None!r}")` renders nothing instead of "None". The recursive call on line 96 also drops both `conversion` and `spec` for every item of a list.

### `src/pytex_analyze/analyze.py:63` — A label whose argument is a composite node is never counted as defined

`_first_required_text` returns `None` as soon as the first required parameter is neither `str` nor `Raw`. `ControlSequence("label", (Parameter(Concat("fig:", "a")),))` therefore adds nothing to `label_counts`, while `\cref{fig:a}` (a plain string) is collected as a reference. `analyze` then reports "reference to undefined label 'fig:a'" for a document that is correct, and the duplicate-label check misses a real duplicate of the same name.

### `src/pytex_analyze/analyze.py:99` — Every reference command's argument is split on commas, but only cref and Cref accept a list

The comma split runs for all of `_REF_COMMANDS`, including `ref`, `pageref`, `nameref`, `autoref`, `eqref` and `vref`, which take exactly one label name. A label that contains a comma, for example `\label{tab:a,b}` referenced by `\ref{tab:a,b}`, is split into `tab:a` and `tab:b`. Both halves miss the defined set, so the pass emits two false "reference to undefined label" warnings for one correct reference.

### `src/pytex_analyze/optimize.py:11` — Module docstring claimed a guarantee the code does not give

The docstring said `Optimize(x).rendered == x.rendered` is always true. `_tokenize` (line 181) accepts a candidate when `_strip_math_ws(rendered) == _strip_math_ws(target)`, so `Optimize(Raw(r"\\[ x \\]"))` returns a `DisplayMath` node that renders `\[x\]`, which is not byte-equal to the input. A caller that relies on byte equality (for example a cache key or a golden-file test over the rendered `.tex` file) sees a mismatch. I corrected the prose to name the math-whitespace exception; the code is unchanged.

### `src/pytex_api/__init__.py:175` — The TEX output path always returns an empty log and empty warnings

render_blob builds `console = Console(stream=stream)` but never passes it to render_to_latex, which takes no console argument; _materialise_best_effort logs through the `logging` module instead. Only compile_to_pdf receives the console. Failure: render_blob(BuildRequest(..., output_kind=OutputKind.TEX)) on a document whose inline-image or logo conversion was skipped returns BuildResult(log='', warnings=()) - verified on this tree. The caller is told the render was clean, while BuildResult.log is documented as 'The render log and the tectonic log', so a dropped logo is invisible to any client that only inspects the result.

### `src/pytex_api/_compile.py:277` — The post-timeout 'podman rm -f' runs with no timeout

After a wall-clock LimitError, `_run_sandboxed` calls `subprocess.run(['podman','rm','-f',name], capture_output=True, check=False)` with no `timeout=`. Failure: the podman client blocks on the container-storage lock (a common state when another podman operation is stuck), so this call never returns; the executor thread that ran `render_blob` is pinned forever, the `finally: shutil.rmtree(workdir)` in `render_blob` never executes, and the temporary work directory leaks. The whole point of this code path is to bound a runaway build, and it can itself hang unbounded.

### `src/pytex_api/_compile.py:339` — The documented in-process fallback branch is unreachable

`compile_to_pdf` warns and falls back to the `setrlimit` and timeout floor only when `policy.apply_rlimits` is true and `policy.require_sandbox` is false. `policy_for` never produces that pair: `untrusted` and `sandboxed` set both flags true, and `trusted` sets both false (src/pytex_api/_policy.py:158-196). Failure scenario: a host without podman never prints the "falling back to in-process rlimits/timeout confinement" warning, because the `elif policy.require_sandbox` branch raises first. The branch is dead code that documents behavior the product no longer has.

### `src/pytex_api/_models.py:111` — BuildLimits.max_tex_passes is documented as a cap but is never read

`max_tex_passes` appears in no other module in src/ or tests/ - tectonic is invoked once by `build_tectonic_cmd` and decides its own pass count internally. Failure: a caller sets `BuildLimits(max_tex_passes=1)` to bound a pathological document and gets no change in behaviour; tectonic still runs however many passes it wants, so the caller believes a cap is in force that does not exist.

### `src/pytex_api/_security.py:72` — The parent-traversal check in validate_asset_name can never fire

`name.split(".")` splits on the '.' character, so no element of the result can ever equal '..'; the branch is unreachable dead code. Failure: `validate_asset_name('...')` returns '...' unchecked - it passes the empty/dot check (only '.' and '..' are listed), the NUL check, and the separator check. Nothing is exploitable today because separators are refused, but the traversal guard the docstring advertises does not exist, so it would not survive a future relaxation of the separator rule.

### `src/pytex_api/_security.py:72` — The directory-traversal check in validate_asset_name is dead code and never fires

The guard reads `if ".." in name.split("."):`. Splitting on "." can never yield the two-character string ".." as an element: "..".split(".") == ['', '', ''] and "a..b".split(".") == ['a', '', 'b']. The branch is therefore unreachable for every input. No traversal actually gets through, because line 68 rejects absolute paths and line 71 rejects both path separators, and line 64 rejects the bare ".." name. The defect is a check that reads as a traversal guard, gives false confidence, and would silently fail to protect if the separator check were ever relaxed. Concrete failure: validate_asset_name("..…") or any name containing ".." reaches the intended branch zero times; a reviewer auditing the traversal defense sees a guard that does nothing.

### `src/pytex_builder/build.py:77` — Markdown inputs keep `.md` in the jobname, and the docstring contradicts itself

Confirmed. The docstring at line 77 says "PyTeX drops the extension of the input file", but the suffix test at line 93 covers only `.py` and `.tex`. `_default_output(Path('examples/notes.md'), Path('build'))` returns `build/notes.md.out.tex` and `report.md` returns `build/report.md.out.tex`, so the PDFs are `build/notes.md.out.pdf` and `build/report.md.out.pdf`. The Example block in the same docstring (line 90) shows `2026-06-15 STUPA.md` keeping the `.md`, so the two halves of the docstring disagree. The docstrings of examples/notes.md and examples/report.md promise `notes.out.tex` and `build/report.out.pdf`. Not fixed, as instructed.

### `src/pytex_builder/build.py:78` — Markdown inputs keep `.md` in the jobname, contradicting the docstring

The docstring says "PyTeX drops the extension of the input file", but the suffix test covers only `.py` and `.tex`. `_default_output(Path('examples/notes.md'), Path('build'))` returns `build/notes.md.out.tex` (verified by running it), so the PDF is `build/notes.md.out.pdf`. The docstrings in examples/notes.md and examples/report.md promise `notes.out.tex` and `build/report.out.pdf`. Either the code or the docstring is wrong; the Example block in the same docstring shows the `.md` being kept, so the two halves of the docstring disagree with each other.

### `src/pytex_builder/build.py:97` — _slug collisions silently make two different inputs share one rendered .tex and one PDF

`_default_output` slugifies the stem by collapsing whitespace to `_` and deleting every character outside `[\w.\-]`, with no collision check. Build `Sitzung 1.md` and then `Sitzung_1.md` into the same build directory: both slug to `Sitzung_1.md`, so the second run overwrites `build/Sitzung_1.md.out.tex` and `build/Sitzung_1.md.pdf` from the first, and prints a normal 'Built' success line. The same happens for `Bericht (final).md` and `Bericht final.md`, which both reduce to `Bericht_final.md`.

### `src/pytex_builder/build.py:97` — Markdown input keeps `.md` in the TeX jobname, which can break the biber step

`_default_output` strips `.py` and `.tex` from the input name but not `.md`/`.markdown`, so `notes.md` renders to `<build_dir>/notes.md.out.tex` and `job` becomes `notes.md.out`. Failure scenario: build `notes.md` with `--variant report` and a `bibliography:` frontmatter key. The `\jobname` is `notes.md.out`; biber, which strips everything after the last dot of its argument, looks for `notes.md.bcf` instead of `notes.md.out.bcf` and reports 'Cannot find control file'. The bibliography then renders empty with no build failure. `_slug` already exists to keep the jobname safe for biber/makeindex, so the embedded dot looks like an oversight rather than a deliberate choice.

### `src/pytex_builder/build.py:263` — _optimize replaces Document.body without re-attaching the parent link

Document.__post_init__ calls attach(self, self.body, self.preamble) to set each child's _parent. `tex_node.body = Optimize(tex_node.body)` assigns a brand-new node tree straight to the attribute, bypassing __post_init__, so the optimized body's _parent stays None. Any code that walks upward via TeX.parent from inside the body reaches None instead of the Document. No consumer reads .parent today, so this is latent, but it silently breaks the first analysis check or component that starts to.

### `src/pytex_builder/build.py:419` — MAX_PASSES = 3 is unreachable; at most two compile passes ever run

The loop continues only when `pass_no == 1 and run_makeindex(...)`, so on pass 2 the condition is false regardless of makeindex and `break` always fires. Build a document where the glossary index still changes on the second pass (a glossary entry first cited inside a chapter title, so pass 2 rewrites the .glo): the third pass that MAX_PASSES = 3 promises never runs and the PDF ships with a stale glossary. The constant name and value tell a reader three passes are possible.

### `src/pytex_builder/console.py:68` — Console.hint prints the label 'cause:' although every caller passes a suggested action

`hint` writes the fixed bullet `    cause:` but its docstring says it prints 'a suggestion that belongs to the warning or error above it', and both call sites pass an instruction, not a cause. `run_makeindex` produces '    cause: install a TeX distribution providing 'makeindex'' and `build.py:441` produces '    cause: check the log in build'. Build a document with glossary entries on a host without makeindex: the user reads that the cause of the warning is that they should install TeX Live, which inverts the meaning of the line.

### `src/pytex_builder/render.py:36` — _TSTRING_PREFIX matches an ordinary "t" string, so unrelated syntax errors get a misleading t-string hint

The pattern `(?<![A-Za-z0-9_])[rR]?[tT][rR]?['"]` only requires that the character before the `t` is not a word character. In `{"t": 1}` the `t` is preceded by a double quote (not a word character) and followed by a double quote, so the pattern matches. Same for `sep="t"` and for a docstring that mentions `"T"`. Import a `.tex.py` on Python 3.13 that has a genuine unrelated SyntaxError (a missing comma, say) and also contains a dict literal keyed on "t": the user is told 'this file appears to use t-string syntax (t"..."), which needs Python 3.14', which sends them to upgrade Python instead of to the real typo.

### `src/pytex_builder/render.py:80` — sys.path.pop(0) can remove an entry the imported module inserted

_render_python inserts the input file's directory at sys.path[0] and pops index 0 in the finally block. A `.tex.py` file that itself does `sys.path.insert(0, ...)` at module scope (a common pattern for a shared assets directory) leaves its own entry at index 0. The finally block then deletes the document's entry and leaves the builder's entry on sys.path permanently, so a later get_tex_node call in the same process resolves sibling imports against the wrong directory.

### `src/pytex_builder/tectonic.py:217` — musl tarball rename is pinned to version == '2.19' only

_biber_candidates picks the new musl file name 'biber-linux-musl_x86_64.tar.gz' only when version == '2.19' and the old name for every other version, but an upstream rename is normally permanent from that release onward. Compile a document whose BCF maps to biber 2.20 or 2.21: the SourceForge musl URL is built with the pre-2.19 name, 404s, and the musl candidate is silently skipped. On a musl-only host the build then falls back to the glibc build, which cannot exec, and fails with 'failed to obtain a working biber'.

### `src/pytex_builder/tectonic.py:344` — No timeout on any network subprocess, so a stalled connection hangs the build forever with no output

`_download_to` runs `curl -fsSL -o dest url` with neither `--max-time` nor `timeout=`; `ensure_tectonic` (line 185) runs `curl ... | sh` the same way; `biber_for_build` (line 479) runs `biber --version` with no timeout. All three use `capture_output=True`, so curl's progress and error output are hidden. `_biber_runs` passes `timeout=30`, so the author was aware of the hazard elsewhere. Run `pytex doc.md --build` behind a captive portal or against a blackholed route with no tectonic on PATH: the process prints '==> Downloading tectonic' and then sits in the TCP connect forever with no further output and no way to distinguish it from a slow download.

### `src/pytex_builder/tectonic.py:372` — `_biber_runs` does not catch `subprocess.TimeoutExpired`

`_biber_runs` guards only `OSError`, but `subprocess.run([...], timeout=30)` raises `subprocess.TimeoutExpired`, which is a `SubprocessError` and not an `OSError`. Failure scenario: a downloaded or cached biber that hangs on `--version`, for example on a stalled network file system, makes `_biber_runs` raise after 30 s. In `run_tectonic` (src/pytex_builder/tectonic.py:545) nothing catches it, so `pytex --build` aborts with a raw traceback instead of a `BuildError` with a readable message. On the API path `_biber_env` swallows it, so the two paths also behave differently.

### `src/pytex_builder/tectonic.py:407` — _ensure_biber uses fixed shared scratch file names, so concurrent builds corrupt each other and one deletes the other's cached binary

`tmp = cached.parent / "biber.download"` and `cand = cached.parent / "biber.candidate"` are fixed paths under the shared user cache, with no lock and no per-process suffix. Run two `pytex doc.md --build` invocations in parallel on one machine (a CI matrix, or a Makefile with `-j2`) when biber 2.19 is not yet cached. Both processes curl into the same `biber.download`; process B's curl truncates the file while process A's `_extract_biber_binary` is reading it, so A fails with 'extract failed'. A's `except Exception` block then runs `if cached.exists(): cached.unlink()`, which deletes the working binary B may have just installed with `cand.replace(cached)`. B's `finally` also unlinks A's `tmp` and `cand` out from under it.

### `src/pytex_builder/tectonic.py:448` — probe_bcf writes a POSIX shell script named 'biber' on Windows too

probe_bcf unconditionally writes '#!/bin/sh\nexit 0\n' to a file named `biber` and chmods it 0o755, although the rest of the module explicitly supports Windows (biber-MSWIN64.zip, _biber_cached returns biber.exe). On Windows tectonic looks for biber.exe, which the temp directory does not contain, so the probe pass never produces a .bcf; the extra full tectonic run then happens on every compile pass and never yields the version information it exists to obtain.

### `src/pytex_builder/tree.py:107` — _as_math misreads a flattened Concat of two math nodes as a single Math node

`_optimize_concat` in pytex_analyze flattens a nested Concat unless `_is_environment` holds, and `_is_environment` only recognizes `\begin`/`\end`. A math node is a Concat of `\(`, body, `\)`, so it is flattened into its parent. `_as_math` then only checks that the first and last children are the matching delimiters. I ran `render_tree(Optimize(Concat(Raw(r'\(a\)'), Raw(' and '), Raw(r'\(b\)'))))` and got one `Math` node whose children are `Raw "a"`, `ControlSequence \)`, `Raw " and "`, `ControlSequence \(`, `Raw "b"`. Any `.tex` or Markdown document with two inline math spans in one paragraph makes `pytex --tree` show one bogus Math node containing stray closing and opening delimiters instead of two Math nodes. The rendered LaTeX is correct; only the tree view lies.

### `src/pytex_builder/variants.py:175` — _report_base_level counts headings inside fenced code blocks, producing the 0.x numbering its own comment warns about

`_HEADING_RE.match` runs over every raw line, including lines inside ``` fences. Render a report whose frontmatter supplies `title` (so `_derive_title` never runs and never strips anything) and whose body uses `## ...` headings plus a fenced shell block containing `# Install the tool`. I ran `_report_base_level` on exactly that body: it returns -1 instead of -2, because the shell comment counts as a level-1 heading. `Markdown(body, base_level=-1)` then maps `##` to `\section`, so in scrbook the sections render with no chapter and number as 0.1, 0.2 - the precise failure the comment above `body=body_tex` says the mapping exists to prevent.

### `src/pytex_builder/variants.py:219` — A relative `bibliography` path resolves against the process cwd and a miss silently drops the whole bibliography

`_bibliography` does `path = Path(value)` and `return path.read_text(...) if path.is_file() else None`, with no anchoring to the Markdown file's directory and no warning on a miss. Put `bibliography: refs.bib` in `docs/paper.md` next to `docs/refs.bib` and run `pytex docs/paper.md --build` from the repository root: `Path("refs.bib").is_file()` is False, `_bibliography` returns None, `_report` sets `show_bibliography=False` and emits no `filecontents`, and the PDF ships with every `\cite` unresolved. Nothing is printed. The same cwd assumption is in `_resolve_logo`, which falls back to passing the raw path through as if it were a vendored logo name.

### `src/pytex_components/boxes.py:212` — A box with no icon attaches the shared module-level `Empty` singleton, whose `_parent` is global mutable state

`_preset` calls `FaIcon(icon_name)`, and `FaIcon(None)` returns the module-level singleton `Empty = EmptyTeX()` (src/pytex/model/empty.py:25) rather than a fresh node. `ColoredBox.__post_init__` then calls `attach(self, self.body, self.icon)`, which writes `_parent` on that one shared instance. `CustomBox(body, None, color)` is the documented no-icon path and `VotingResults.rendered` uses it for the `Enthaltung` column. Construct `a = CustomBox("a", None, "red")` and then `b = CustomBox("b", None, "blue")`: `a.children` still contains `Empty`, but `Empty.parent` is now `b`, so walking up from `a`'s icon lands in a completely different node tree — and after a `VotingResults` render it lands in a node tree that no longer exists. Any parent-chain query about a no-icon box's icon returns the wrong answer, and the answer depends on global construction order.

### `src/pytex_components/cleveref_names.py:18` — The German plural for the listing reference type is a singular noun

`"listing": ("Listing", "Codeblock")` registers `\crefname{listing}{Listing}{Codeblock}`. Every other entry pairs a German singular with its German plural, but `Codeblock` is singular (the plural is `Codebl\"ocke`, and the plural of `Listing` is `Listings`). A document with `\cref{lst:a,lst:b}` prints "Codeblock 1 und 2" instead of a plural noun.

### `src/pytex_components/cleveref_names.py:18` — The `listing` cleveref entry pairs the singular "Listing" with the unrelated plural "Codeblock"

Every other entry in `GERMAN_NAMES` pairs a German singular with its own plural (`Abbildung`/`Abbildungen`, `Anhang`/`Anhänge`). `"listing": ("Listing", "Codeblock")` instead pairs one noun with a different noun, and "Codeblock" is itself singular. `GermanCrefNames()` therefore emits `\crefname{listing}{Listing}{Codeblock}`, so a document with `\label{lst:a}`, `\label{lst:b}` and `\cref{lst:a,lst:b}` prints "Codeblock 1 und 2" — a singular German word used as a plural, and a word the singular reference never used. The intended pair is `("Listing", "Listings")` or `("Codeblock", "Codeblöcke")`.

### `src/pytex_components/watermark.py:26` — _watermark_text doubles a backslash, which LaTeX reads as a row break

`safe = text.replace("\\", "\\\\")` turns one backslash into two. Two backslashes are not an escaped backslash in LaTeX; inside the `tabular{c}` that `DraftWatermark` builds they are a row separator. Call `DraftWatermark("DRAFT\\v1")`: each of the 16 cells in a row now ends the row early, so the grid gains stray rows and the tiling is misaligned. A literal backslash needs `\textbackslash{}`.

### `src/pytex_components/wordcount.py:25` — The wordcount macros hard-code the Build directory, ignoring --build-dir

`\quickwordcount` writes `Build/words.sum` and reads it back with `\input{Build/words.sum}`; `\detailtexcount` uses `Build/.wcdetail`. tectonic runs the compile pass inside the build directory named by `--build-dir`. Run `pytex report.tex.py --build --build-dir out` on a document that calls `\quickwordcount{report}`: texcount writes into `out/Build/` only if that directory already exists, otherwise the shell redirect fails silently and `\input{Build/words.sum}` aborts the compile pass with `File 'Build/words.sum' not found`. The macros also use `\verbatiminput` without requiring the `verbatim` package.

### `src/pytex_hsrtreport/document.py:102` — Comment contradicted the code it describes (comment corrected)

The old comment said "\printglossary/\printbibliography emit their own \chapter* heading (and page break), so no manual \clearpage precedes them", but `BIBLIOGRAPHY_PRINT` on line 109 is `\clearpage\chapter*{Literaturverzeichnis}...\printbibliography[heading=none,title={}]` — it does carry a manual `\clearpage` and a manual `\chapter*`, and it explicitly disables the built-in heading. A reader who trusted the comment and deleted the leading `\clearpage` would get the bibliography heading typeset on the last page of the acronym list. I rewrote the comment to match the code; the code is unchanged.

### `src/pytex_hsrtreport/document.py:171` — The preamble is frozen at construction, so a later body assignment is ignored

`__post_init__` calls `_build_preamble()` once, which snapshots `discovered_colors()`. `body` is a plain mutable dataclass field. After `doc = HSRTReport(body=Empty, title="T"); doc.body = Textcolor(Color.hex("FF0000").name, "x")`, the preamble still holds the old `\definecolor` set, so the rendered `.tex` references `hexFF0000` with no definition and tectonic aborts. The same stale snapshot applies to `geometry_options` and `user_preamble` changed after construction.

### `src/pytex_hsrtreport/document.py:227` — \title and \author evaluate inline pytex(...) markers regardless of the trust policy

`_preamble_parts` builds `Raw(f"\\title{{{coerce_tex(self.title).rendered}}}")` with the default `allow_replacements=True`, while every other Raw in this package passes `allow_replacements=False`. `coerce_tex` wraps a plain string in `Raw` with replacements on, so a title string that contains `\iffalse{pytex(__import__('os').system('id'))}\fi` is evaluated at render time. `pytex_api` sets `allow_replacements=policy.allow_tex_replacements` for the top-level `.tex` source, but that gate does not reach this node. The Markdown path is currently protected only because `pytex_builder/variants.py` calls `escape_latex(title)`; an API caller that constructs `HSRTReport` directly with an untrusted title has no protection.

### `src/pytex_hsrtreport/pagesetup.py:36` — Docstring claimed \ifHSRTBackMatter suppresses headers and footers; the shipped .tex gates only the header

The old docstring said "Set it to true in the back matter to suppress the chapter headers and footers." In `src/pytex_hsrtreport/tex/pagesetup.tex` the flag appears only in the two `\ohead` definitions (lines 24 and 32). Line 31 sets `\cfoot{Seite~\thepage\ifHSRTNumberedBody~von~\pageref{LastPage}\fi}`, and the comment on lines 26-30 states explicitly that the center footer is NOT gated by `\ifHSRTBackMatter`. A reader who trusted the docstring would expect no footer on the bibliography page and would file the visible `Seite N von M` line as a regression. I rewrote the docstring to match the `.tex` file; the code is unchanged.

### `src/pytex_markdown/convert.py:376` — _code comment described the fallback in the wrong direction

The comment read "A code block holds one RawText child. Fall back to a direct string", but the code reads the direct text first via _text(node) and only then falls back to _text(kids[0]). A reader trusting the comment would conclude that a node carrying its text directly is never handled, and would add a redundant child lookup. I rewrote the comment to match the code. The code itself is unchanged and correct.

### `src/pytex_markdown/protocol/document.py:121` — Attendance count is derived by counting commas, so a name with a comma inflates it

_data_lines calls _joined first, which collapses a list to a comma-joined string, then recovers the head count as value.count(',') + 1. Frontmatter `anwesend: ["Meier, Hans", "Schmidt, Ada"]` joins to 'Meier, Hans, Schmidt, Ada' and the title page prints 'Anwesend (4)' for two people. The list length is available before the join and is never used.

### `src/pytex_markdown/protocol/header.py:149` — scalar("gremium", "gremium") passes the same key twice

Every other call site pairs the German key with its English alias, for example scalar("datum", "date") and scalar("beginn", "start"). Here the fallback repeats "gremium", so a frontmatter that writes `committee: StuPa` instead of `gremium: StuPa` produces an empty committee name and the header title degrades to the bare "Protokoll". The duplicate argument is dead in every case.

### `src/pytex_tikz/tikz.py:141` — Fill closes its path with a hard-coded -- instead of self.op

`Fill.rendered` joins the points with `self.op` but always appends `-- cycle`, while the parallel `Draw.rendered` (line 120) appends `{self.op} cycle`. `Fill(("a", "b", "c"), op="to").rendered` produces `\fill (a) to (b) to (c) -- cycle;`, which closes a curved path with a straight segment; the filled region does not match the path the caller asked for.

### `src/pytex_tikz/tikz.py:141` — Fill always appends `-- cycle` and ignores its own op

`Fill.rendered` joins the points with `self.op` but closes the path with the literal `--`. `Fill(points=("0,0", "1,0", "1,1"), op="to")` renders `\fill (0,0) to (1,0) to (1,1) -- cycle;`, which mixes a curve operator with a straight closing segment. `Draw` exposes a `cycle` flag for the same job; `Fill` has none, so a caller cannot render an open filled path at all.

### `tests/golden/test_golden_pdf_smoke.py:39` — skipif uses truthiness of PYTEX_TEST_PODMAN, so PYTEX_TEST_PODMAN=0 enables the test

The guard is `not (podman_available() and os.environ.get("PYTEX_TEST_PODMAN"))`, and os.environ.get returns the string "0", which is truthy. The skip reason and the module docstring both say "set PYTEX_TEST_PODMAN=1". A developer who exports PYTEX_TEST_PODMAN=0 to turn the live build off gets the opposite: on a machine with podman installed the test runs, builds the sandbox image, warms the tectonic cache, and takes up to the 300 s wall timeout. Compare against "1" the way tests/golden/test_golden.py does for PYTEX_UPDATE_GOLDEN.

### `tests/pytex/commands/test_builtin.py:68` — test_bold_aliases_textbf compares two rendered outputs and passes when both are empty

The assertion is `Bold("x").rendered == Textbf("x").rendered`. It never names the expected LaTeX. Concrete failure: if `ControlSequence.rendered` regressed to return "" for every node, both sides are "" and the test passes, reporting the alias as correct while nothing renders. The neighbouring `test_textbf` would catch the total regression, but a shared partial defect — for example both factories losing the argument and rendering `\textbf{}` — is invisible to this test. Anchoring it to the literal `r"\textbf{x}"` would remove the shared-failure blind spot.

### `tests/pytex/commands/test_builtin.py:114` — test_enumerate checks only the opening delimiter

`test_enumerate` asserts `out.startswith(r"\begin{enumerate}")` and stops there, while the parallel `test_itemize` directly above it also asserts the `\end` and both `\item` lines. Concrete failure: if the enumerate factory forgot to close the environment, or dropped the items "a" and "b" entirely, the rendered string `\begin{enumerate}` alone satisfies the assertion and the test passes while the document fails to compile.

### `tests/pytex/commands/test_builtin_extras.py:32` — test_immediate cannot detect a lost separator space, which turns the output into an undefined control sequence

The test asserts `out.startswith(r"\immediate")` and `"body" in out`. src/pytex/commands/builtin.py:571 renders `Concat(ControlSequence("immediate", ()), Raw(" "), body)`, and that `Raw(" ")` is load-bearing: `\immediate` is a control word, so without the space TeX reads `\immediatebody` as one token. Concrete failure: drop the `Raw(" ")` and the rendered string becomes `\immediatebody`; both assertions still hold (`\immediatebody` starts with `\immediate` and contains `body`), the test passes, and the compile pass fails with "Undefined control sequence". No other test in the repository renders `Immediate`, so this is the only guard on that space.

### `tests/pytex/commands/test_new_modules.py:292` — Four factories are checked for their package requirement but never for what they render

`Captionsetup({"font": "small"})` at line 292, `Tabularx("5cm", "lX", "x")` at line 319, `Longtable("ll", "x")` at line 321 and `Multirow(2, "*", "x")` at line 324 are each bound to a name only so that `assert PACKAGE in obj.requires` can run. None of the four asserts `.rendered`. Concrete failure: if `Tabularx` swapped its width and column-spec arguments and rendered `\begin{tabularx}{lX}{5cm}`, the package requirement is still TABULARX, the test stays green, and the error only appears when tectonic aborts the compile pass. Every other factory in the same file is asserted on both axes.

### `tests/pytex/commands/test_new_modules.py:365` — Setmainfont options assertion cannot distinguish an optional argument from a mandatory one

Line 365 asserts `"Path=fonts/" in Setmainfont("Times", {"Path": "fonts/"}).rendered`. The source at src/pytex/commands/fontspec.py:42 renders the options with `Parameter(..., optional=True)`, producing `\setmainfont{Times}[Path=fonts/]`. The substring test says nothing about the delimiters. Concrete failure: if `optional=True` were lost, the output becomes `\setmainfont{Times}{Path=fonts/}`; fontspec takes only one mandatory argument, so the trailing group is left in the document body and LaTeX typesets the literal text "Path=fonts/" on the first page. The test still passes because the substring is present.

### `tests/pytex/commands/test_new_modules.py:422` — Ifstrequal and Equal are bound only to run a requires assertion, so argument order is unchecked

Line 421 binds `e = Equal("a", "b")` and line 422 binds `s = Ifstrequal("a", "b", "y", "n")` purely so that `assert IFTHEN in e.requires` and `assert ETOOLBOX in s.requires` can run. Neither `.rendered` is asserted. Concrete failure: if `Ifstrequal` swapped its true and false branches and rendered `\ifstrequal{a}{b}{n}{y}`, the package requirement is still ETOOLBOX, the test stays green, and every conditional in a real document takes the wrong branch, which produces a wrong but perfectly compilable PDF. This is distinct from the reported Captionsetup/Tabularx/Longtable/Multirow hole: different factories, different lines, and here the untested axis is argument order rather than a missing render check.

### `tests/pytex/helpers/test_coerce.py:18` — test_coerced_tex_protocol_check cannot fail: the isinstance is nominal, not structural

`Raw` declares `class Raw(TeX)` (src/pytex/model/raw.py:61), so `isinstance(coerce_tex("x"), TeX)` is true through normal inheritance, and the preceding test already asserts `isinstance(out, Raw)`. Even the structural path cannot fail: `TeX` is a `runtime_checkable` Protocol whose members are properties with concrete defaults, so isinstance only checks attribute presence. Delete the `rendered` property from `Raw` and it inherits the protocol's stub, which returns None — this test still passes green while every render produces `None`. The test claims to verify protocol conformance and verifies nothing beyond what test_coerce_str_to_raw already states.

### `tests/pytex/helpers/test_with_package.py:43` — test_with_package_children_descend restates the implementation instead of checking it

`assert wp.children == (wp.child,)` compares the `children` property against the very attribute the property returns (`return (self.child,)` in src/pytex/helpers/with_package.py). It never checks that `wp.child` is the `ControlSequence("bar", ())` the decorated factory produced. If `with_package`'s wrapper were broken to wrap the wrong value — for example `WithPackage(Raw(""), pkg)` instead of `WithPackage(func(*args, **kwargs), pkg)` — this assert would still pass, and only `test_with_package_wraps_result` would catch it.

### `tests/pytex/model/test_color_extras.py:94` — test_definecolor_with_color_instance would pass on a malformed \definecolor line

The assertion only checks that "FF8800" and "{HTML}" appear somewhere in the rendered string. If Definecolor emitted the model and the value in the wrong order, or dropped the color name, or wrote \definecolour, the substrings would still be present and the test would pass. Compare against the full expected string \definecolor{cFF8800}{HTML}{FF8800} instead.

### `tests/pytex/model/test_document_extras.py:47` — test_inline_image_block_empty_returns_empty requests tmp_path but never uses it

The test builds Document("hi") with no image at all, so the tmp_path fixture creates a temporary directory that the test never touches. The unused parameter suggests a missing setup step to a reader and costs one directory per run. test_rendered_emits_filecontents_before_document has the same signature but does use tmp_path, which makes the difference easy to miss.

### `tests/pytex/test_registry.py:11` — Registry tests permanently mutate class-level global state with no cleanup

`Registry.types` is a ClassVar dict shared process-wide, and neither `test_add_returns_obj` nor `test_add_registers` removes the key it inserts. After the module runs, "MyFunc" and "UniqueRegFn" stay in the registry for every later test in the session, so `Registry.names()` and `Registry.namespace()` see entries that no production import created. Concretely, running the suite with pytest-repeat or `--count=2` re-executes `test_add_registers`, hits the duplicate branch in `Registry.add`, and emits "Duplicate key in registry (overwritten): UniqueRegFn" on stderr; any test that later asserts on a clean registry or on empty stderr fails on the second pass only.

### `tests/pytex/test_registry.py:85` — PYTHONPATH is rebuilt from sys.path and breaks on empty or separator-bearing entries

`os.pathsep.join(sys.path)` flattens entries that are not valid PYTHONPATH values. Under `python -m pytest` sys.path contains an empty string; joining produces "a::b", which the child interpreter reads as the current working directory — the subprocess then imports whatever `pytex` happens to sit in pytest's cwd rather than the one under test. Worse, a checkout under a directory whose name contains a colon (legal on Linux) splits into two bogus entries, the child fails to import pytex, and the test fails at `assert result.returncode == 0` with an ImportError that looks unrelated to registry keys.

### `tests/pytex_analyze/test_optimize.py:15` — _types and _names are byte-identical duplicate helpers

`_types` and `_names` have the same body, and the tests use them interchangeably (`_names` in the Concat tests, `_types` in the math tests). A future change to one helper, for example making it recurse or filter out Empty children, silently applies to only half the assertions and the two halves of the file then disagree about what a child list means.

### `tests/pytex_api/test_sandbox.py:305` — monkeypatch.setattr(compile_mod.subprocess, "run", ...) replaces subprocess.run process-wide

`compile_mod.subprocess` is the stdlib module object itself, not a module-local alias, so this patch (and the three identical ones on `sandbox_mod.subprocess` at lines 476, 518 and 536) swaps `subprocess.run` for every importer for the duration of the test. Concrete failure: `test_timeout_force_removes_container` stubs `_run_confined` but leaves the rest of the process live; if any code that runs inside that window shells out (a pytest plugin collecting coverage or git metadata, or `pytex_builder.tectonic.ensure_tectonic` probing for biber), it receives the local `_P` class that exposes only `returncode` and dies with `AttributeError: _P has no attribute 'stdout'` far from the cause. Patching a module-local indirection, or asserting on an injected runner, keeps the blast radius inside the test.

### `tests/pytex_api/test_unicode_packages.py:46` — Only three of the six mapped Unicode characters are asserted

`ALL_MAPPED` is "€ → ↔ ≤ ≥ ·" and the module docstring claims every mapped character is covered, but `test_all_mapped_chars_render_without_trust_error` asserts only `\euro{}`, `\rightarrow` and `\cdot`. Concrete failure: delete the `"↔"`, `"≤"` or `"≥"` entries from `_GLYPHS` in src/pytex_markdown/glyphs.py (or let a refactor drop the `_math()` wrapper for them). The characters then reach the rendered `.tex` as raw UTF-8, XeTeX typesets tofu or fails under the DIN font, and both parametrized tests in this file still pass green. The test should also assert `\leftrightarrow`, `\leq` and `\geq`, and that no character of `ALL_MAPPED` survives verbatim in the output.

### `tests/pytex_builder/test_build.py:174` — assert "TRUSTED" in err also matches "UNTRUSTED"

The message raised in src/pytex_api/_render.py is "Python-executing input (.tex.py / .py) is only allowed for TRUSTED builds, not untrusted". The substring check is satisfied by any message that merely contains the word UNTRUSTED. If the wording were changed to "this input kind is rejected at level UNTRUSTED" and the reference to what IS allowed dropped, the test still passes while the user-facing hint lost its actionable half.

### `tests/pytex_builder/test_build.py:186` — test_untrusted_blocks_shell_escape_package never asserts why the run failed

The test asserts only `code == 1` and `not out.exists()`, unlike its sibling test_untrusted_blocks_python_exec which inspects stderr. Any failure satisfies it. If the package allowlist stopped inspecting `\usepackage{...}` and the run instead failed for an unrelated reason (a parse error in the untrusted `.tex` reader, or a missing build directory), the test stays green while `minted` is no longer rejected for being a shell-escape vector. Capturing capsys and asserting the message names `minted` would pin the actual gate.

### `tests/pytex_builder/test_default_output.py:44` — The slug test locks in non-ASCII survival in a TeX jobname

`_slug` strips with `re.sub(r"[^\w.\-]", "", name)`, and Python's `\w` is Unicode-aware, so `ö` survives; the test asserts exactly that via the obscure `"wörd x.md".replace(" ", "")`. The sibling test one function above exists because a bad jobname breaks the `.bcf` file biber reads. A Markdown file named `Bericht Größe.md` yields the jobname `Bericht_Größe.md`, which makeindex and biber can mis-handle under a non-UTF-8 locale, the same class of failure the slug is meant to prevent.

### `tests/pytex_builder/test_render.py:34` — Sibling import leaks `helper` into sys.modules across tests

`_render_python` inserts the input file's directory at the front of `sys.path` and executes the module, so `from helper import VALUE` registers `helper` in `sys.modules` permanently; the `finally` block pops `sys.path` but never removes the module. A second test that creates its own `tmp_path/helper.py` with a different `VALUE` and renders a `.py` input file would silently reuse the first test's cached module and assert against the stale value. The failure depends on test ordering, so it appears only when the suite is run with -p no:randomly or a different -k selection.

### `tests/pytex_builder/test_tectonic.py:259` — curl-failure path never asserts that the partial download is deleted

test_download_to_rejects_checksum_mismatch asserts `not dest.exists()`, but test_download_to_curl_failure_returns_false checks only the False return. If `_download_to` stopped unlinking `dest` on a non-zero curl exit, a truncated file would stay at `biber.download`; `_ensure_biber` moves on to the next candidate, and a later run that reuses the same path could extract the truncated archive and report "biber binary not found" instead of "download failed".

### `tests/pytex_builder/test_tectonic.py:316` — test_run_makeindex_no_targets_returns_false cannot tell the two guards apart

run_makeindex returns False when `not present or not style.exists()`. The test passes an empty tmp_path, so both halves are false at once and the test cannot say which one fired. Drop the `not present` half of the guard and the test still passes. A build that emits a `job.ist` style file but no glossary entries (a document that loads `glossaries` but defines no entry) would then invoke makeindex on a nonexistent `job.glo`, and the user gets a spurious "makeindex failed for job.glo" warning on every build. A second case with only `job.ist` present would close this.

### `tests/pytex_builder/test_variants.py:153` — Dead assertion: "1.0" is always present in a report

`assert "Version" in out and "1.0" in out` - the HSRTReport title page always renders `\setstretch{1.0}` (verified: building `---\ntitle: T\n---\n## X` with no datalines already contains "1.0"). So the second half of the conjunction is true for every report, whether or not the data line value was rendered. Only the `"2026-06-02"` assertion two lines down actually tests that a data-line value reaches the output; if the `Version` line specifically lost its value (for example a regression that drops a value containing a dot), the test still passes.

### `tests/pytex_components/test_boxes.py:74` — test_top_level_renders_no_parent asserts nothing about the parent or the level

The assertions are `"mdframed" in out` and `"hello" in out`, which any `ColoredBox` render at any depth satisfies. Failure scenario: change the default of the `_render_depth` ContextVar to 1, or compute `level = max(depth, self.nesting_level) + 1`; a parent-free box then renders `backgroundcolor=blue!20` instead of `blue!12`, and this test still passes. The regression is caught only by the baseline line inside `test_concurrent_render_depth_isolation`, so the test that is named for the top-level case contributes nothing.

### `tests/pytex_hsrtreport/test_color_walker.py:21` — test_discovered_dedupes_by_name uses two equal Colors, so value-level dedup satisfies it and name-level dedup is never proven

The test builds `a = Color.hex("#AABBCC", name="dupcol")` and `b = Color.hex("#AABBCC", name="dupcol")`. `Color.__eq__` and `Color.__hash__` compare `(name, spec)`, so a and b are equal values. `collect_colors` and `HSRTReport.discovered_colors` currently key on `color.name`, but a regression that keys on the Color itself (a plain set, or `seen[color] = color`) would still collapse these two and the test would pass. The defect that dedup-by-name exists to prevent is two Colors that share a name and differ in spec: `Color.hex("#AABBCC", name="dupcol")` plus `Color.hex("#112233", name="dupcol")` would then emit two `\definecolor{dupcol}` lines with conflicting values, and xcolor would silently take the last one. Give the second Color a different hex.

### `tests/pytex_hsrtreport/test_color_walker.py:30` — Dead Color.hex(name="custom1") statement leaves the negative half of the test unasserted

Line 30 constructs Color.hex("#112233", name="custom1") and discards it. Color has no global registry side effect (src/pytex/model/color.py builds a plain frozen value), so the statement changes nothing. It reads as an intended control: a Color that is not in the node tree must not reach the preamble. That control is never asserted. If the color walker regressed to emitting every constructed Color, or to emitting one \definecolor per hex value regardless of tree membership, this test still passes. The same shape appears at line 51, where Color.named("red") is constructed and discarded before the negative assertion on line 54.

### `tests/pytex_hsrtreport/test_document.py:30` — test_preamble_has_cleveref_names_de matches the German singular as a prefix of the plural

`GERMAN_NAMES` maps figure -> ("Abbildung", "Abbildungen"), table -> ("Tabelle", "Tabellen") and equation -> ("Gleichung", "Gleichungen"). Each singular is a prefix of its own plural, so `assert "Abbildung" in out` is satisfied by the plural alone. If `GermanCrefNames` regressed to emit `\crefname{table}{}{Tabellen}` (an empty singular), cleveref would print "siehe  3.1" with no type name for every single reference, and this test would still pass. `test_misc.test_german_cref_names_emits_pairs` pins the full `crefname{figure}{Abbildung}{Abbildungen}` fragment; use that shape for table and equation too.

### `tests/pytex_hsrtreport/test_logos_image.py:102` — test_default_logos_for_makers cannot tell MAKERS from MAKERS-RAlign

The assertion is `"MAKERS" in out and ".pdf" in out`. "MAKERS" is a prefix of "MAKERS-RAlign", so if default_logo_names(Variant.MAKERS) regressed to return the right-aligned footer logo, DefaultLogos would render MAKERS-RAlign.pdf and the test would still pass. The sibling test at line 109 pins the distinction, but this one is meant to guard the rendered output and does not. Assert on the converted file name, for example `"MAKERS.pdf" in out`.

### `tests/pytex_hsrtreport/test_titlepage_voting.py:25` — test_titlepage_data_lines_render_in_table never checks that the data lines are inside a tabular

The test asserts only that `Autor`, `Frederik`, `Datum` and `2026` appear somewhere in `TitlePage(...).rendered`. `TitlePage._content` wraps `_data_table_body` in `Tabular(...)`, and `_data_table_body` emits bare `&` separators plus `\\` line breaks. If a regression yielded `_data_table_body(self.data_lines)` directly, or dropped the `Tabular` wrapper while keeping the rows, all four substrings would still be present and the test would pass, but the compile pass would fail with "Misplaced alignment tab character &" because the alignment material sits outside any tabular. Assert on `\begin{tabular}` and on the label appearing after it, as `test_misc.test_titlepage_basic_render` does for `begin{titlepage}`.

### `tests/pytex_koma/test_document.py:18` — test_accepts_each_koma_class accepts a bare `]{<cls>}` substring, so a wrong document class can satisfy it

The assertion is `f"\\documentclass{{{cls}}}" in doc.rendered or f"]{{{cls}}}" in doc.rendered`. The second branch matches any `]{scrbook}` sequence anywhere in the rendered output, not only the one that closes the \documentclass option list. A preamble line such as `\PassOptionsToClass[...]{scrbook}`, or a class option list emitted for a different command, satisfies the test even when \documentclass names the wrong class. Anchor the check on `\documentclass` and allow an option list between the macro and the brace.

### `tests/pytex_koma/test_document.py:27` — test_paper_flag lacks the negative assertion that its fontsize sibling has, so `paper=a4paper` also satisfies it

`_class_option_flags` yields the bare flag `a4paper` only while `"a4paper" in PAPER_FLAGS`, and otherwise yields the pair `("paper", "a4paper")`. The test asserts only `"a4paper" in doc.rendered`, and the string `paper=a4paper` also contains `a4paper`. If `PAPER_FLAGS` lost an entry or the branch inverted, KomaDocument would render `\documentclass[paper=a4paper]{scrartcl}`; typearea rejects `a4paper` as a value for the `paper` key, so the compile pass errors out or falls back to the wrong paper size, and the test still passes. `test_fontsize_flag` on line 37 shows the right shape: it adds `assert "fontsize=11pt" not in doc.rendered`.

### `tests/pytex_markdown/test_euro.py:55` — Code-span euro test passes when the euro sign disappears

`test_euro_left_alone_in_code_span` asserts only `\euro{}` not in out. If the code-span path dropped the `€` character, or replaced it with `\texttt{[missing glyph]}`, or returned an empty string, the assertion still passes and the regression ships. The parallel test at tests/pytex_markdown/test_unicode_glyphs.py:89 shows the fix: it pins the whole `\texttt{a → b ≤ €}` fragment.

### `tests/pytex_markdown/test_tables.py:61` — The image test asserts a POSIX path while the converter emits `str(Path)`, so a Windows path defect cannot fail the test on Linux

convert.py:315 renders `IncludeImage(str(Path(dest).resolve()))`, but the test asserts `Path('pics/foo.png').resolve().as_posix()`. On Linux the two are byte-identical, so the test passes and hides the difference. Concrete: on Windows the converter emits `\includegraphics{C:\work\pics\foo.png}` — backslashes that LaTeX reads as control sequences, so the compile fails — while the test asserts `C:/work/pics/foo.png` and fails with a path mismatch instead of naming the real defect. The assertion is written against the correct behavior; the code is not.

### `tests/pytex_markdown/test_unicode_glyphs.py:75` — `record[0]` assumes the glyph warning is the first warning of the block

`pytest.warns` records every warning raised inside the block, not only the ones that match the class. `test_missing_glyph_warning_names_the_char` reads `record[0].message`. If marko or a pytex import path emits any other warning (a DeprecationWarning, for example) during `Markdown('✓ done').rendered` before the glyph warning, `record[0]` is that other warning and `assert '✓' in message` fails with an unrelated message. The sibling test at line 65 avoids this with the `match=` argument.

### `tests/pytex_protocol/test_entries.py:43` — test_timestamp_is_blue_and_bold never checks bold

`Timestamp` renders `Textcolor("hanblue", Concat(FaIcon("clock"), " ", Textbf(time)))`, but the test asserts only "hanblue" and "18:30". Failure scenario: drop the `Textbf` wrapper (or the `FaIcon("clock")`) from src/pytex_markdown/protocol/entries.py:110; the timestamp loses its bold weight and its clock icon in every protocol, and the test named `..._is_blue_and_bold` still passes because both remaining assertions hold.

### `tests/pytex_protocol/test_functional_equivalence.py:119` — Duplicate shortcode sample leaves the intended edge case untested

The last entry of `SHORTCODE_SAMPLES` is `"{{datum}}"`, byte-identical to the entry at index 2, and its comment claims it covers the no-surrounding-prose case that index 2 already covers. Whatever distinct edge the author meant (probably a shortcode at the very start plus trailing text, or a trailing shortcode) is never fed to `expand_inline_shortcodes`, so a regression in that path stays invisible.

### `tests/pytex_protocol/test_render.py:32` — test_abstimmung_keeps_body_text_lines does not notice a tally line left in the body

The test asserts "Beschlussvorschlag XY" in out and "vote-yea" in out. `_vote_callout` reads the counts from the joined text (`full`) and filters the body with `_is_tally_line`. Failure scenario: raise the threshold in `_is_tally_line` from `>= 2` to `>= 4`, so no line ever counts as a tally. The counts still parse from `full`, so "vote-yea" renders, and "Beschlussvorschlag XY" is still in the body, so both assertions hold. The box now prints "Ja: 1, Nein: 2, Enthaltung: 3" as duplicated prose above the tally columns, and no test sees it.

### `tests/pytex_protocol/test_shortcodes.py:45` — Verbatim-shortcode test never checks the braces it documents

The comment states that the braces stay escaped so the typo is visible in the PDF, but the only assertion is `"nonsense foo" in out`. If `expand_shortcode` dropped the surrounding `{{` and `}}` completely, the reader would lose every hint that a shortcode was mistyped and the test would still pass.
