# `_render_depth` thread-safety & a blob-in/blob-out API module

Design note covering two related questions:

1. Is the `_render_depth` counter in `pytex_components/boxes.py` safe under
   concurrent (multi-threaded / async) rendering, and can it be fixed without
   changing output or breaking tests?
2. How would a module that wraps PyTeX as a blob-in / blob-out service (for API
   use) be shaped — I/O, async, trust levels, and security mitigations?

The two parts share a thread: the same concurrency that makes the API module
useful is what turns the `_render_depth` global into a latent bug, and the same
`contextvars` mechanism solves both.

---

## Part 1 — `_render_depth` thread-safety

### What it is and how it is used

`pytex_components/boxes.py` renders `ColoredBox` (and the `InfoBox` /
`WarningBox` / … presets). A box's background opacity grows with how deeply it
is nested in other boxes. There are **two** ways the code knows the nesting
depth:

- **`nesting_level`** (property, lines ~59-62) walks the parent chain:
  `1 + sum(1 for p in self.parents if isinstance(p, ColoredBox))`. Correct for a
  node whose parent links are intact.
- **`_render_depth`** — a render-time counter that mirrors the LaTeX
  `coloredBoxLevel` env counter. It exists because rendering an outer box
  *builds new wrapper nodes* (`Minipage`, `Mdframed`, `Concat`, …) and
  re-`attach`es the body into them, **severing** the original parent chain
  before the inner box renders. So during a top-down render the parent chain is
  unreliable and the counter is the source of truth.

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

All accesses:

| line | access | purpose |
|------|--------|---------|
| 34   | `_render_depth: int = 0`   | module-level definition |
| 98   | `global _render_depth`     | declare write intent |
| 99   | `_render_depth += 1`       | enter a box: read-modify-write |
| 104  | `max(_render_depth, …)`    | read for the opacity formula |
| 160  | `_render_depth -= 1`       | leave a box: read-modify-write |

The mechanism itself is fine: it is a classic recursion counter that rides the
synchronous call stack. `ColoredBox.rendered` ultimately calls
`Concat(...).rendered`, which renders the body; if the body is another
`ColoredBox`, its `rendered` re-enters the same block while `_render_depth` is
already `1`, so the inner box sees `2`. The `try/finally` restores the value on
the way out. Single-threaded, it is correct.

### Is it thread-safe? No.

The counter is **shared mutable module state**. Two threads rendering different
documents (or an API serving concurrent requests) read and write the *same*
integer:

- **Cross-render contamination (the real damage).** Thread A renders a
  top-level box and expects `level == 1`. While A is between its `set` and its
  read, thread B is several boxes deep and has driven `_render_depth` up to,
  say, 6. A's `max(_render_depth, self.nesting_level)` reads 6 and renders the
  top-level box with a level-6 opacity. No crash — just a **silently wrong
  document**. This does not even need the increment to be non-atomic; it is a
  shared-variable visibility problem.
- **Lost updates.** `+= 1` / `-= 1` are read-modify-write. The GIL serialises
  individual bytecodes but can switch threads *between* them, so concurrent
  increments/decrements can be lost, leaving the counter drifting (it can even
  go negative and never return to 0).

This is not theoretical. A 2000-iteration stress test (top-level boxes rendered
while a pool renders 8-deep boxes) on the **current** code:

```
ORIGINAL (global int):   wrong-opacity top-level renders: 1991/2000
PATCHED  (ContextVar):   wrong-opacity top-level renders:    0/2000
```

Today PyTeX renders single-threaded (one CLI invocation, one document), so the
bug is **latent**. The moment Part 2's API renders concurrently — threads or
async tasks — it becomes live and produces wrong PDFs with no error.

### Options to fix (no output change, no broken tests)

The hard constraint: `TeX.rendered` is a **no-argument property** (the `TeX`
Protocol in `pytex/interface/tex.py`). The depth must flow across a recursive
chain of *different node instances* without being passed as an argument. That
rules some options out.

| option | isolates threads | isolates async tasks | needs API change | verdict |
|--------|:---:|:---:|:---:|---------|
| **`contextvars.ContextVar`** | ✅ (fresh per thread) | ✅ (copied per `Task`) | no | **recommended** |
| `threading.local` | ✅ | ⚠️ shared across tasks on one loop thread | no | OK fallback if async never matters |
| instance / passed-through state | ✅ | ✅ | **yes — breaks `rendered` signature & every node** | rejected |
| `threading.Lock` around the counter | corrects increments only | ❌ | no | rejected — see below |

**`threading.local`** — each OS thread gets its own counter. Fixes the threaded
case completely and is behaviourally identical single-threaded. Weakness: it is
keyed by *thread*, not by *logical task*. If the API offloads each build to its
own worker thread (the recommended model — see Part 2), this is enough. But if
multiple `asyncio` tasks ever render on one event-loop thread, they share the
thread-local and the bug returns. It also does not auto-propagate into
`run_in_executor` workers.

**`contextvars.ContextVar`** — the standard-library tool built exactly for
"implicit context that must not leak across concurrent flows." Each OS thread
starts from the `default`, and each `asyncio.Task` runs with an independent
*copy* of the context, so tasks never clobber each other. `set()` returns a
token and `reset(token)` restores the previous value — a perfect fit for the
existing `try/finally`. Critically, this is the **same** primitive Part 2 needs,
so Part 1 and Part 2 are solved by one mechanism. Tiny cost: `get`/`set` are
marginally slower than a bare global, irrelevant next to building LaTeX strings.

**Instance / threaded-through state** — conceptually cleanest ("no globals") but
infeasible without redesigning the render interface: `rendered` takes no
arguments, and the counter deliberately spans *different* `ColoredBox`
instances connected only by the live call stack (the parent chain is severed,
which is *why* the counter exists). Passing a context object would mean changing
`rendered` everywhere and touching every node type. Out of scope, high risk.

**Lock** — a lock around `+= 1` stops lost updates but does **not** stop
cross-render contamination: two renders still see one shared counter. To make it
correct you would hold the lock for the *entire* render, serialising all
rendering and destroying the concurrency the API is for. Wrong tool.

### Recommendation & prototype

**Use `contextvars.ContextVar`.** It fixes both the threaded and async cases,
is behaviourally identical single-threaded (default `0`, `+1` per nesting level,
restored on exit), requires no API change, and is the same primitive Part 2
relies on.

Prototyped on branch **`feat/render-depth-contextvar`**:

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

- Full suite: **745 passed** (existing 744 + one new concurrency regression
  test `test_concurrent_render_depth_isolation`).
- `basedpyright` (the project's checker): **0 errors, 0 warnings** on the
  changed files.
- `mypy --strict` (Python 3.13): **Success: no issues found**.
- Stress test: `1991/2000 → 0/2000` wrong renders.

It solves cleanly and without risk. No behavioural change for existing
single-threaded use; the diff is mechanical and the regression test pins it.

---

## Part 2 — Blob-in / blob-out API module (`pytex_api`, exploratory)

### Goal

Wrap PyTeX so a caller hands it **source bytes** and gets **result bytes** back,
without ever touching the filesystem itself:

```
Markdown / .tex / .tex.py  bytes  ──▶  pytex_api  ──▶  .tex bytes  and/or  PDF bytes
```

All file I/O (temp dirs, asset materialisation, tectonic's `--outdir`,
intermediates) is an internal detail, isolated per call.

### Why a wrapper is needed

The current entry points are filesystem-shaped:

- `pytex_builder.render.get_tex_node(path)` dispatches on the file **suffix**
  and reads from a `Path`.
- `_render_python` does `spec_from_file_location(...)` + `exec_module` — it
  **executes the input as Python**. (Likewise Markdown's `[//]: # "EXPR"`
  comments call `eval`, and `.tex` `\iffalse pytex(...)\fi` blocks evaluate
  replacements.) These are arbitrary-code-execution surfaces — central to the
  trust model below.
- `pytex_builder.build._run` writes the `.tex`, materialises inline assets
  (`write_inline_fonts/logos/images`) next to it, downloads tectonic/biber into
  a shared temp cache, and shells out to tectonic with **shell-escape ON by
  default** (`build.py` `--no-shell-escape` is opt-out).

A blob API must keep all of that but contain it.

### Proposed surface

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

`input_kind` is **explicit**, not sniffed from a suffix — the caller declares
what the bytes are, removing suffix-confusion attacks and the implicit
"`.py` means execute me" coupling.

### I/O isolation

`render_blob` runs entirely inside a fresh `tempfile.mkdtemp()` workdir, removed
in a `finally`:

1. Write `source` to `work/input.<kind>` and each `assets[name]` to
   `work/<name>` (names validated: no `..`, no absolute paths, no symlinks — see
   security).
2. Reuse `get_tex_node` (or a trust-gated variant) to get the `TeX` node and
   `.rendered` the LaTeX. If `output_kind == TEX`, return those bytes.
3. For PDF: run the existing `run_tectonic` / `run_makeindex` loop with
   `--outdir work/build`, then read `work/build/<job>.pdf` back as bytes.
4. `shutil.rmtree(work)`.

The caller never sees a path. Tectonic's binary/biber cache (`CACHE_DIR`) stays
process-global and read-only-ish (it is just downloaded tools), but each
**build** gets its own workdir, so concurrent builds cannot collide on
intermediates — which is exactly the property `--outdir` per call gives us.

### Async support (cross-reference to Part 1)

Rendering (`.rendered`) is pure-CPU and synchronous; tectonic/biber/makeindex
are **blocking subprocesses**. Neither should run on the event loop. Model:

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

- **The render step** spins the `_render_depth` `ContextVar`. Because Part 1
  switched it to a `ContextVar`, concurrent renders — whether in different
  executor threads or different asyncio tasks — are isolated automatically. Had
  we kept the module global (or even `threading.local` with a thread pool that
  multiplexes tasks), concurrent API requests would corrupt each other's box
  opacities. **This is the direct Part 1 ↔ Part 2 link.** `copy_context()` +
  `ctx.run(...)` also means any future render-time context vars propagate into
  the worker correctly.
- **The compile step** (tectonic) is a subprocess. For true async without
  hogging a thread, use `asyncio.create_subprocess_exec` with
  `asyncio.wait_for(..., timeout=limits.wall_timeout_s)` instead of the
  synchronous `subprocess.run` in `tectonic.py` — or keep `subprocess.run` and
  offload the whole `render_blob` to a thread/process pool as above. A
  **process** pool is preferable for untrusted input (hard isolation, killable,
  memory-capped).

### Trust-level model

The exec surfaces (Python `exec_module`, Markdown `eval`, `.tex` `pytex(...)`,
and tectonic `\write18` via shell-escape) make trust the central axis:

| capability | `UNTRUSTED` | `SANDBOXED` | `TRUSTED` |
|------------|:----------:|:-----------:|:---------:|
| `.tex.py` / `.py` input (`exec_module`) | ❌ reject kind | ❌ | ✅ |
| Markdown `[//]: # "EXPR"` eval comments | ❌ stripped | ❌ stripped | ✅ |
| `.tex` `\iffalse pytex(...)\fi` replacements | ❌ `allow_replacements=False` | ❌ | ✅ |
| tectonic shell-escape (`-Z shell-escape`, `\write18`) | ❌ off | ❌ off | ✅ on |
| arbitrary LaTeX `\usepackage{…}` | allowlist only | wider allowlist | any |
| `\input` / `\include` / `\InputIfFileExists` of arbitrary paths | ❌ confined to workdir | confined | any |
| `\write` to arbitrary paths | ❌ | ❌ | ✅ |
| network access (during build) | ❌ none | ❌ none | host policy |
| embedded images (base64 inline) | ✅ (needs shell-escape — see note) | ✅ | ✅ |
| caller-supplied `assets` blobs | ✅ name-validated | ✅ | ✅ |
| build time / memory / output size | hard limits | hard limits | generous/none |

Note: PyTeX's inline images currently rely on shell-escape to decode their
base64 payloads at compile time (`build.py` comment at the `-Z shell-escape`
branch). For `UNTRUSTED`, that is a conflict: we want shell-escape **off** but
inline images **on**. Resolution options (pick during implementation):

1. Pre-decode inline images in Python and write them as real files into the
   workdir *before* tectonic runs, so no shell-escape is needed at compile time
   (preferred — removes the only "legit" reason untrusted input needs
   `\write18`).
2. Restrict untrusted inline images to a Python-side `\includegraphics` of
   already-materialised assets.

`TRUSTED` is for first-party callers (your own documents); `UNTRUSTED` is the
default and assumes the source is hostile.

### Security mitigations for untrusted input (concrete to PyTeX/tectonic)

1. **No code execution.** `UNTRUSTED`/`SANDBOXED` reject `InputKind.TEX_PY`
   outright; Markdown is converted with eval-comments disabled; `.tex` is loaded
   with `allow_replacements=False`. This closes the Python `exec`/`eval` paths,
   which are far more dangerous than anything LaTeX can do.
2. **Shell-escape off.** Never pass `-Z shell-escape` for untrusted builds —
   kills `\write18`. (tectonic disables shell-escape by default; the risk is
   PyTeX's opt-out flag, so the API must force it off regardless of caller.)
3. **Confined filesystem.** Build inside a per-request `mkdtemp`. Set tectonic's
   `--outdir` into it. Validate every `assets` name (reject absolute paths,
   `..`, and symlinks). Consider `openin_any=p` / `openout_any=p` (paranoid)
   via `TEXMF` env so `\input`/`\write` cannot escape the workdir even if
   shell-escape were somehow on.
4. **Resource limits.** Wall-clock timeout via
   `asyncio.wait_for` / `subprocess` `timeout=`; on POSIX, `resource.setrlimit`
   (`RLIMIT_CPU`, `RLIMIT_AS`, `RLIMIT_FSIZE`, `RLIMIT_NOFILE`) in a
   `preexec_fn`, or run under a process pool / container with cgroup limits.
   Cap `max_input_bytes`, `max_output_bytes`, and `max_tex_passes`
   (`build._run` already loops `MAX_PASSES`; expose & cap it).
5. **LaTeX-bomb / infinite-loop defence.** Timeouts are the backstop. tectonic
   has no `\write18` by default and its own pass model, but a `\def\x{\x\x}…`
   expansion bomb or `\loop` can still burn CPU/RAM/disk → caught by
   `RLIMIT_CPU` + wall timeout + `RLIMIT_FSIZE` (log/aux growth) +
   `RLIMIT_AS`. Kill the whole process group on timeout
   (`os.killpg`) so child processes die too.
6. **Package allowlist.** Inspect the assembled preamble (PyTeX already tracks
   `requires` per node, so for first-party nodes the package set is known) and
   reject `\usepackage` of anything outside an allowlist. For raw `.tex`,
   scan/parse `\usepackage`/`\RequirePackage` and refuse unknown packages —
   block known-dangerous ones (`shellesc`, `write18`, `python`, `pythontex`,
   `minted` with `-shell-escape`, `catchfile`, `\openin` helpers).
7. **No network.** tectonic fetches packages from its bundle over the network on
   first use. For untrusted builds, **pre-warm the bundle** once and run with a
   network-isolated sandbox (container netns / firewall), or pin tectonic to an
   offline bundle so a build cannot trigger arbitrary fetches. Never download
   tectonic/biber *during* an untrusted request (the `ensure_tectonic` /
   `_ensure_biber` curl paths must be a separate, privileged warm-up step).
8. **Output caps.** Truncate the returned `log`; enforce `max_output_bytes` on
   the PDF before reading it back; refuse oversize intermediates.

### Open questions / risks

- **Inline-image vs shell-escape conflict** (above) must be resolved before
  untrusted inline images are allowed; option 1 (pre-decode in Python) is the
  clean fix and also simplifies trusted builds.
- **Strength of isolation.** `setrlimit` + timeouts are a floor, not a jail.
  Real untrusted multi-tenant use wants an OS sandbox (container, gVisor,
  seccomp, separate uid, read-only rootfs, netns). The API should be designed so
  `render_blob` can be the thing you run *inside* such a sandbox, not the sandbox
  itself.
- **biber/tectonic auto-download** runs `curl | sh` (`ensure_tectonic`) and
  fetches biber binaries. This must be a privileged warm-up, never reachable
  from an untrusted request path.
- **Process vs thread pool.** Threads share `_render_depth`'s context isolation
  correctly (Part 1) but offer no memory/kill isolation for the compile step;
  processes do. Likely: render in-thread, compile in a killable subprocess with
  rlimits.
- **`config`/`variant` trust.** Markdown variants and frontmatter can pull in
  templates/assets; the allowlist and path confinement must cover those too.
- **Determinism / caching.** Same input bytes → same output is desirable for
  caching; tectonic SyncTeX/timestamps may need normalising.

### Cross-reference summary

Part 1's switch to `contextvars.ContextVar` is the prerequisite that makes
Part 2's concurrent/async rendering correct: without it, two API requests
rendering boxes at the same time silently corrupt each other's nesting depth.
One primitive, both problems.
