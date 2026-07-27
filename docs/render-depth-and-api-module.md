# `_render_depth` thread safety and a blob-in / blob-out API module

This design note answers two related questions.

1. Is the `_render_depth` counter in `pytex_components/boxes.py` safe when more
   than one render runs at the same time? Can PyTeX fix it without a change to
   the rendered `.tex` file and without a broken test?
2. What shape does a module have that wraps PyTeX as a blob-in / blob-out
   service? The shape covers the input and the output, async support, trust
   levels, and security mitigations.

One link joins the two parts. The same concurrency that makes the API module
useful turns the `_render_depth` global into a latent bug. One `contextvars`
mechanism solves both.

---

## Part 1 — `_render_depth` thread safety

### What it is and how it is used

`pytex_components/boxes.py` renders `ColoredBox` and the presets `InfoBox`,
`WarningBox`, and the others. The background opacity of a colored box grows
with its nesting depth inside other colored boxes. The code knows that depth in
**two** ways.

- **`nesting_level`** is a property at lines 82-90. It walks the parent chain:
  `1 + sum(1 for p in self.parents if isinstance(p, ColoredBox))`. The value is
  correct for a node whose parent links are intact.
- **`_render_depth`** is a render-time counter that mirrors the LaTeX
  `coloredBoxLevel` counter. It exists because the render of an outer box
  *builds new wrapper nodes* (`Minipage`, `Mdframed`, `Concat`, and more) and
  `attach`es the body into them again. That step **breaks** the original parent
  chain before the inner box renders. So the parent chain is not reliable
  during a top-down render, and the counter is the source of truth.

Original implementation:

```python
_render_depth: int = 0          # module global

# inside ColoredBox.rendered:
global _render_depth
_render_depth += 1
try:
    level = max(_render_depth, self.nesting_level)
    ...                          # builds wrappers; .rendered recurses into the
    ...                          # body, which re-enters this block at depth+1
    return Concat(...).rendered
finally:
    _render_depth -= 1
```

All accesses in that original code:

| line | access | purpose |
| --- | --- | --- |
| 34   | `_render_depth: int = 0`   | the module-level definition |
| 98   | `global _render_depth`     | declare the intent to write |
| 99   | `_render_depth += 1`       | enter a box: read, modify, write |
| 104  | `max(_render_depth, …)`    | read for the opacity formula |
| 160  | `_render_depth -= 1`       | leave a box: read, modify, write |

The mechanism itself is sound. It is a recursion counter that rides the
synchronous call stack. `ColoredBox.rendered` calls `Concat(...).rendered`,
which renders the body. If the body is another `ColoredBox`, its `rendered`
enters the same block again while `_render_depth` already holds `1`. The inner
box then sees `2`. The `try/finally` restores the value on the way out. With
one thread the code is correct.

### Is it thread-safe? No.

The counter is **shared mutable module state**. Two threads that render
different documents read and write the *same* integer. An API that serves
concurrent requests does the same.

- **Cross-render contamination is the real damage.** Thread A renders a
  top-level box and expects `level == 1`. At that moment thread B is several
  boxes deep and has driven `_render_depth` up to 6. The
  `max(_render_depth, self.nesting_level)` call of thread A reads 6. Thread A
  then renders the top-level box with the opacity of level 6. Nothing crashes.
  The result is a **silently wrong document**. The increment does not even need
  to be non-atomic. This is a shared-variable visibility problem.
- **Lost updates.** `+= 1` and `-= 1` each read, modify, and write. The GIL
  serializes single bytecodes, but the interpreter can switch threads *between*
  them. Concurrent increments and decrements can get lost, and the counter then
  drifts. It can even go below zero and never return to 0.

This is not a theoretical problem. A stress test with 2000 iterations rendered
top-level boxes while a pool rendered 8-deep boxes. The result on the
**original** code:

```
ORIGINAL (global int):   wrong-opacity top-level renders: 1991/2000
PATCHED  (ContextVar):   wrong-opacity top-level renders:    0/2000
```

The `pytex` command still renders with one thread, one invocation, and one
document. The `pytex_api` module of Part 2 renders concurrently, so the bug is
live on that path. `pytex_components/boxes.py` now uses a `ContextVar`, which
closes it. Without that change, concurrent API requests would produce wrong
PDFs and report no error.

### Options to fix (no output change, no broken tests)

The hard constraint: `TeX.rendered` is a **property that takes no argument**.
The `TeX` Protocol in `pytex/interface/tex.py` defines it. The depth must flow
across a recursive chain of *different* TeX nodes without an argument. That
rules some options out.

| option | isolates threads | isolates async tasks | needs API change | verdict |
| --- | --- | --- | --- | --- |
| **`contextvars.ContextVar`** | ✅ (one per thread) | ✅ (copied per `Task`) | no | **recommended** |
| `threading.local` | ✅ | ⚠️ shared by the tasks on one loop thread | no | acceptable fallback if async never matters |
| instance state, or state passed through | ✅ | ✅ | **yes. It breaks the `rendered` signature and every node.** | rejected |
| `threading.Lock` around the counter | corrects the increments only | ❌ | no | rejected. See below. |

**`threading.local`**. Each OS thread gets its own counter. This fixes the
threaded case, and single-threaded behavior does not change. The weakness is
the key. It is the *thread*, not the *logical task*. If the API moves each
build to its own worker thread, this is enough. Part 2 recommends that model.
But if several `asyncio` tasks ever render on one event-loop thread, they share
the thread-local value and the bug returns. A thread-local value also does not
propagate into a `run_in_executor` worker on its own.

**`contextvars.ContextVar`**. This is the standard-library tool for implicit
context that must not leak across concurrent flows. Each OS thread starts from
the `default`. Each `asyncio.Task` runs with its own *copy* of the context, so
tasks never overwrite each other. `set()` returns a token, and `reset(token)`
restores the old value. That fits the existing `try/finally` exactly. It is
also the **same** primitive that Part 2 needs, so one mechanism solves Part 1
and Part 2. The cost is small. `get` and `set` are a little slower than a bare
global, which does not matter next to the work of building LaTeX strings.

**Instance state, or state passed through.** This is the cleanest idea on
paper, because it has no global. It is not workable without a redesign of the
render interface. `rendered` takes no argument, and the counter spans
*different* `ColoredBox` nodes on purpose. Only the live call stack connects
them. The parent chain is broken, which is *why* the counter exists. A context
object would change `rendered` everywhere and touch every node type. That is
out of scope and high risk.

**Lock.** A lock around `+= 1` stops the lost updates. It does **not** stop
cross-render contamination, because two renders still share one counter. A
correct version holds the lock for the *whole* render. That serializes every
render and removes the concurrency that the API needs. This is the wrong tool.

### Recommendation and outcome

**PyTeX uses `contextvars.ContextVar`.** It fixes the threaded case and the
async case. Single-threaded behavior does not change. The default is `0`, the
depth grows by 1 per nesting level, and the value returns on exit. It needs no
API change, and it is the same primitive that Part 2 relies on.

The change started on the branch **`feat/render-depth-contextvar`**.
`src/pytex_components/boxes.py` now holds it:

```python
from contextvars import ContextVar

_render_depth: ContextVar[int] = ContextVar("coloredbox_render_depth", default=0)

# inside ColoredBox.rendered:
depth = _render_depth.get() + 1
token = _render_depth.set(depth)
try:
    level = max(depth, self.nesting_level)
    ...
    return Concat(...).rendered
finally:
    _render_depth.reset(token)
```

Status:

- Full suite: **926 passed and 3 skipped**. The suite holds the concurrency
  regression test `test_concurrent_render_depth_isolation` in
  `tests/pytex_components/test_boxes.py`.
- `basedpyright` (the checker of this project): **0 errors, 0 warnings** on the
  changed files.
- `mypy --strict` (Python 3.13): **Success: no issues found**.
- Stress test: `1991/2000 -> 0/2000` wrong renders.

The change is mechanical and low risk. Single-threaded use behaves as before,
and the regression test pins that behavior.

---

## Part 2 — Blob-in / blob-out API module (`pytex_api`, shipped)

### Goal

`pytex_api` wraps PyTeX. A caller hands it **source bytes** and gets **result
bytes** back. The caller never touches the filesystem.

```
Markdown / .tex / .tex.py  bytes  ──▶  pytex_api  ──▶  .tex bytes  and/or  PDF bytes
```

All file reads and writes are an internal detail, and PyTeX isolates them per
call. This covers the temporary work directory, the inline assets that PyTeX
writes to disk, the `--outdir` of the tectonic binary, and the intermediates.

### Why a wrapper is needed

`pytex_builder` shapes its entry points around the filesystem.

- `pytex_builder.render.get_tex_node(path)` dispatches on the file **suffix**
  and reads from a `Path`.
- `_render_python` calls `spec_from_file_location(...)` and then `exec_module`.
  It **runs the input as Python**. The Markdown `[//]: # "EXPR"` comments call
  `eval` in the same way, and a `.tex` `\iffalse pytex(...)\fi` block evaluates
  the inline `pytex(...)` marker. These are the code-execution surfaces. The
  trust model below governs them.
- `pytex_builder.build._run` writes the rendered `.tex` file. It then writes
  the inline assets to disk next to that file with `write_inline_fonts`,
  `write_inline_logos`, and `write_inline_images`. It downloads the tectonic
  binary and biber into a shared cache directory, and then runs the tectonic
  binary. For a `trusted` build, shell-escape is on by default, and
  `--no-shell-escape` turns it off.

A blob API must keep all of that and contain it.

### Proposed surface

The sketch below is the original proposal. `pytex_api` splits the value types
into `pytex_api/_models.py` and re-exports them from `pytex_api/__init__.py`.
The shipped `BuildLimits` also carries `max_fsize_bytes` and `max_log_chars`.
The shipped `BuildRequest` types `config` and `assets` as a `Mapping`, and it
builds the default `limits` with a `field(default_factory=BuildLimits)`. The
module also defines the error classes `ApiError`, `TrustError`, `LimitError`,
and `CompileError`.

```python
# pytex_api/__init__.py
from dataclasses import dataclass, field
from enum import Enum

class InputKind(Enum):
    MARKDOWN = "md"
    TEX = "tex"
    TEX_PY = "py"          # executes Python — TRUSTED only

class OutputKind(Enum):
    TEX = "tex"            # rendered LaTeX source
    PDF = "pdf"            # compiled via tectonic

class TrustLevel(Enum):
    UNTRUSTED = "untrusted"   # default; hostile input assumed
    SANDBOXED = "sandboxed"   # semi-trusted; some packages, still no shell
    TRUSTED   = "trusted"     # full power, incl. Python exec & shell-escape

@dataclass(frozen=True)
class BuildLimits:
    wall_timeout_s: float = 30.0
    cpu_timeout_s: float = 30.0
    max_output_bytes: int = 25 * 1024 * 1024
    max_memory_bytes: int = 512 * 1024 * 1024
    max_input_bytes: int = 2 * 1024 * 1024
    max_tex_passes: int = 3

@dataclass(frozen=True)
class BuildRequest:
    source: bytes
    input_kind: InputKind
    output_kind: OutputKind = OutputKind.PDF
    trust: TrustLevel = TrustLevel.UNTRUSTED
    variant: str | None = None
    config: dict[str, object] = field(default_factory=dict)
    assets: dict[str, bytes] = field(default_factory=dict)   # name -> bytes
    limits: BuildLimits = BuildLimits()

@dataclass(frozen=True)
class BuildResult:
    output: bytes                 # .tex or .pdf bytes
    output_kind: OutputKind
    log: str                      # tectonic/render log, truncated
    warnings: tuple[str, ...]
    duration_s: float

# Sync core (runs the whole pipeline in an isolated temp dir):
def render_blob(req: BuildRequest) -> BuildResult: ...

# Async wrapper (offloads the blocking work; see async section):
async def render_blob_async(req: BuildRequest) -> BuildResult: ...
```

`input_kind` is **explicit**. PyTeX never reads it from a file suffix. The
caller declares what the bytes are. This removes suffix-confusion attacks and
the implicit rule that a `.py` suffix means "execute me".

### I/O isolation

`render_blob` runs inside a fresh `tempfile.mkdtemp()` temporary work
directory, and a `finally` block removes it:

1. PyTeX validates every `assets[name]` up front, and rejects an absolute
   path, a `..` component, and a path separator. See the security section.
2. Render the source to LaTeX under the trust policy.
   `pytex_api._render.render_to_latex` dispatches on `input_kind`. The `TEX_PY`
   path writes the source to `work/input.py`, the only case that needs an
   input file on disk, and then calls `get_tex_node`. The `TEX` path wraps
   the bytes in `Raw`, and the `MARKDOWN` path calls `build_document`. If
   `output_kind == TEX`, return those bytes.
3. For a PDF: write the LaTeX to `work/document.tex`, write each validated
   `assets[name]` to `work/<name>`, and run the tectonic binary with
   `--outdir work/build`. Then read `work/build/document.pdf` back as bytes.
   `pytex_api._compile.build_tectonic_cmd` assembles that argv, and this
   path does not run the makeindex step.
4. `shutil.rmtree(work)`.

The caller never sees a path. The download cache for the tectonic binary and
biber (`CACHE_DIR`) stays global to the process and holds downloaded tools
alone. Each **build** gets its own temporary work directory, so concurrent
builds cannot collide on the intermediates. That is exactly the property a
per-call `--outdir` gives PyTeX.

### Async support (cross-reference to Part 1)

A render (`.rendered`) is pure CPU work and synchronous. The tectonic binary,
biber, and the makeindex step are **blocking subprocesses**. Neither belongs on
the event loop. The model:

```python
import asyncio, contextvars, functools

async def render_blob_async(req: BuildRequest) -> BuildResult:
    loop = asyncio.get_running_loop()
    ctx = contextvars.copy_context()          # carries _render_depth et al.
    return await loop.run_in_executor(
        None, functools.partial(ctx.run, render_blob, req)
    )
```

Two layers:

- **The render step** sets and resets the `_render_depth` `ContextVar`. Part 1
  changed that name to a `ContextVar`, so concurrent renders are isolated. This
  holds for renders in different executor threads and for renders in different
  asyncio tasks. The module global would let concurrent API requests corrupt
  the box opacities of each other. A `threading.local` with a thread pool that
  multiplexes tasks would do the same. **This is the direct link between Part 1 and
  Part 2.** `copy_context()` plus `ctx.run(...)` also propagates any later
  render-time context variable into the worker correctly.
- **The compile step** runs the tectonic binary in a subprocess. For true async
  that holds no thread open, use `asyncio.create_subprocess_exec` with
  `asyncio.wait_for(..., timeout=limits.wall_timeout_s)` in place of the
  synchronous `subprocess.run` in `tectonic.py`. The other option keeps the
  synchronous call and moves the whole `render_blob` to a thread pool or a
  process pool, as above. For untrusted input a **process** pool is better,
  because it gives hard isolation, a killable process, and a memory cap.
  `pytex_api` takes the second option. `render_blob_async` moves the whole
  build to the default executor. `_compile._run_confined` then starts the
  subprocess under a wall-clock timeout, a new session, and a new process
  group.

### Trust-level model

The code-execution surfaces make the trust level the central axis. Those
surfaces are the Python `exec_module`, the Markdown `eval` comments, and the
inline `pytex(...)` marker in a `.tex` source. Shell-escape adds `\write18` in
the tectonic binary.

| capability | `UNTRUSTED` | `SANDBOXED` | `TRUSTED` |
| --- | --- | --- | --- |
| `.tex.py` / `.py` input (`exec_module`) | ❌ PyTeX rejects the kind | ❌ | ✅ |
| Markdown `[//]: # "EXPR"` eval comments | ❌ PyTeX strips them | ❌ PyTeX strips them | ✅ |
| `.tex` `\iffalse pytex(...)\fi` replacements | ❌ `allow_replacements=False` | ❌ | ✅ |
| tectonic shell-escape (`-Z shell-escape`, `\write18`) | ❌ off | ❌ off | ✅ on |
| arbitrary LaTeX `\usepackage{…}` | package allowlist only | wider package allowlist | any |
| `\input` / `\include` / `\InputIfFileExists` of arbitrary paths | ❌ confined to the temporary work directory | confined | any |
| `\write` to arbitrary paths | ❌ | ❌ | ✅ |
| network access during the build | ❌ none | ❌ none | host policy |
| inline images (base64) | ✅ read the note below | ✅ | ✅ |
| caller-supplied `assets` blobs | ✅ PyTeX validates each name | ✅ | ✅ |
| build time, memory, and output size | hard limits | hard limits | large limits, or none |

An inline image renders a `filecontents*` block that holds base64-encoded
data. The compile pass needs shell-escape to decode that data. The comment
sits at the `-Z shell-escape` branch in `pytex_builder/tectonic.py`. For
`UNTRUSTED` this is a conflict, because PyTeX wants shell-escape **off** and
inline images **on**. Two options resolve it, and `pytex_api` takes the first
one:

1. Decode the inline images in Python and write them as real files into the
   temporary work directory *before* the tectonic binary runs. No shell-escape
   is then needed at compile time. `pytex_api._render` calls
   `write_inline_images` on the document to do this. It removes the only
   legitimate reason for untrusted input to need `\write18`.
2. Restrict untrusted inline images to an `\includegraphics` of assets that
   PyTeX has already written to disk.

`TRUSTED` is for first-party callers, which means your own documents.
`UNTRUSTED` is the default, and it assumes that the source is hostile.

### Security mitigations for untrusted input (concrete to PyTeX/tectonic)

1. **No code execution.** `UNTRUSTED` and `SANDBOXED` reject
   `InputKind.TEX_PY` outright. PyTeX converts Markdown with the eval comments
   stripped, and loads a `.tex` source with `allow_replacements=False`. This
   closes the Python `exec` and `eval` paths, which are far more dangerous than
   anything LaTeX can do.
2. **Shell-escape off.** Never pass `-Z shell-escape` for an untrusted build.
   That kills `\write18`. The tectonic binary turns shell-escape off by
   default. The risk is the opt-out flag of PyTeX, so the API forces
   shell-escape off whatever the caller asks for.
3. **Confined filesystem.** Build inside a per-request `mkdtemp` directory, and
   point `--outdir` of the tectonic binary into it. Validate every `assets`
   name, and reject an absolute path, a `..` component, and a path separator.
   The Podman sandbox confines `\input` and `\write`, because it mounts the
   temporary work directory as the only read-write path. A `sandboxed` or
   `untrusted` PDF build fails closed when Podman is missing. PyTeX also
   refuses to read the PDF when the file is a symbolic link.
4. **Resource limits.** Set the wall-clock timeout with `asyncio.wait_for` or
   the `timeout=` argument of `subprocess`. On POSIX, call
   `resource.setrlimit` for `RLIMIT_CPU`, `RLIMIT_AS`, and `RLIMIT_FSIZE` in a
   `preexec_fn`. The other option runs the build under a process pool or a
   container with cgroup limits. Cap `max_input_bytes` and `max_output_bytes`.
   `BuildLimits` also carries `max_tex_passes`, and `build._run` loops over
   `MAX_PASSES`. No code reads `max_tex_passes` today, because the tectonic
   binary picks its own pass count.
5. **Defense against a LaTeX bomb and an infinite loop.** Timeouts are the
   backstop. The tectonic binary has no `\write18` by default and picks its own
   pass count. An expansion bomb such as `\def\x{\x\x}…` or a `\loop` can still
   burn CPU, RAM, and disk. `RLIMIT_CPU`, the wall-clock timeout, `RLIMIT_FSIZE`
   for the log and aux growth, and `RLIMIT_AS` catch that. Kill the whole
   process group on a timeout with `os.killpg`, so the child processes die too.
6. **Package allowlist.** Read the assembled preamble. PyTeX already tracks the
   package requirement of each node, so PyTeX knows the package set of a
   first-party node tree. Reject a `\usepackage` of anything outside the allowlist. For
   a raw `.tex` source, scan `\usepackage` and `\RequirePackage` and refuse an
   unknown package. Block the known-dangerous ones, such as `shellesc`,
   `write18`, `python`, `pythontex`, `minted`, and `catchfile`.
   `pytex_api._policy` holds these three sets as `PACKAGE_ALLOWLIST`,
   `SANDBOXED_EXTRA_PACKAGES`, and `DANGEROUS_PACKAGES`.
7. **No network.** The tectonic binary fetches packages from its bundle over
   the network on first use. For an untrusted build, **warm the bundle once in
   advance** and run with a network-isolated sandbox.
   `pytex_api._sandbox.warm_sandbox_cache` does that warm-up, and a request
   container then runs with `--network none` and `--only-cached`. Never
   download the tectonic binary or biber *during* an untrusted request. The
   `ensure_tectonic` and `_ensure_biber` curl paths must stay a separate,
   privileged warm-up step. `_locate_tectonic` refuses to download when the
   trust policy blocks the network.
8. **Output caps.** Truncate the returned `log`. Check `max_output_bytes`
   against the size of the PDF file before PyTeX reads it. Refuse an oversize
   intermediate.

### Open questions / risks

- **`pytex_api` resolves the conflict between an inline image and
  shell-escape.** `pytex_api._render` decodes the inline images in Python and writes them to
  disk, which is option 1 above. That also simplifies a trusted build.
- **Strength of isolation.** `setrlimit` and a timeout are a floor, not a jail.
  Real untrusted multi-tenant use needs the Podman sandbox. `pytex_api` uses
  rootless Podman with `--network none`, `--read-only`, `--cap-drop ALL`,
  `no-new-privileges`, and cgroup caps. `render_blob` knows nothing about the
  Podman sandbox, and the trust policy selects it. So `render_blob` is the
  thing that runs *inside* the sandbox and is not the sandbox itself.
- **The auto-download of biber and the tectonic binary** pipes `curl` into `sh`
  (`ensure_tectonic`) and fetches biber binaries. This must stay a privileged
  warm-up. An untrusted request path must never reach it.
- **A process pool against a thread pool.** Threads carry the context isolation
  of `_render_depth` correctly, as Part 1 shows. Threads give the compile step
  no memory isolation and no kill isolation. Processes do. `pytex_api` renders
  in a worker thread and compiles in a killable subprocess. For a non-trusted
  build that subprocess is a Podman container.
- **Trust of `config` and `variant`.** A Markdown variant and the frontmatter
  can pull in templates and assets. The package allowlist and the path
  confinement must cover those too.
- **Determinism and caching.** The same input bytes should give the same output
  bytes, which helps a cache. PyTeX may need to normalize the SyncTeX data and
  the timestamps of the tectonic binary first.

### Cross-reference summary

The switch to `contextvars.ContextVar` in Part 1 is the prerequisite that makes
the concurrent and async render of Part 2 correct. Without it, two API requests
that render colored boxes at the same time corrupt the nesting depth of each
other, and nothing reports the error. One primitive solves both problems.
