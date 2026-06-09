"""End-to-end behaviour of ``render_blob`` / ``render_blob_async``.

Focus: the trust model actually gates the code-execution vectors, and
concurrent async renders stay isolated. All assertions are on the rendered
``.tex`` (OutputKind.TEX), so none of these need a tectonic binary.
"""

import asyncio

import pytest

from pytex_api import (
    ApiError,
    BuildLimits,
    BuildRequest,
    CompileError,
    InputKind,
    LimitError,
    OutputKind,
    TrustError,
    TrustLevel,
    render_blob,
    render_blob_async,
)


def _tex(source: bytes, kind: InputKind, trust: TrustLevel, **kw) -> bytes:
    return render_blob(
        BuildRequest(
            source=source,
            input_kind=kind,
            output_kind=OutputKind.TEX,
            trust=trust,
            **kw,
        )
    ).output


# -- happy paths -----------------------------------------------------------


def test_markdown_to_tex_roundtrips_content():
    out = _tex(b"# Hi\n\nHello **world**.", InputKind.MARKDOWN, TrustLevel.UNTRUSTED)
    assert b"Hello" in out


def test_tex_passthrough_untrusted():
    out = _tex(rb"\section{Plain}", InputKind.TEX, TrustLevel.UNTRUSTED)
    assert out == rb"\section{Plain}"


def test_result_metadata_is_populated():
    res = render_blob(
        BuildRequest(
            source=b"# Hi\n\nbody",
            input_kind=InputKind.MARKDOWN,
            output_kind=OutputKind.TEX,
            trust=TrustLevel.UNTRUSTED,
        )
    )
    assert res.output_kind is OutputKind.TEX
    assert res.duration_s >= 0.0
    assert isinstance(res.warnings, tuple)


# -- exec vector 1: Python import (.tex.py / .py) --------------------------

_PY_SIDE_EFFECT = (
    b"import pathlib\n"
    b"pathlib.Path('pwned.txt').write_text('x')\n"
    b"from pytex.model.raw import Raw\n"
    b"__pytex__ = Raw('ok')\n"
)


@pytest.mark.parametrize("trust", [TrustLevel.UNTRUSTED, TrustLevel.SANDBOXED])
def test_python_input_rejected_without_trust(trust):
    with pytest.raises(TrustError):
        _tex(_PY_SIDE_EFFECT, InputKind.TEX_PY, trust)


def test_python_input_runs_only_when_trusted(tmp_path, monkeypatch):
    # Run in an empty cwd so the side-effect file (if it were written) is local.
    monkeypatch.chdir(tmp_path)
    out = _tex(_PY_SIDE_EFFECT, InputKind.TEX_PY, TrustLevel.TRUSTED)
    assert out == b"ok"


def test_untrusted_python_does_not_execute_side_effect(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(TrustError):
        _tex(_PY_SIDE_EFFECT, InputKind.TEX_PY, TrustLevel.UNTRUSTED)
    # The module body never ran, so no file was written.
    assert not (tmp_path / "pwned.txt").exists()


# -- exec vector 2: Markdown eval comments ---------------------------------

_MD_EVAL = b"# T\n\n[//]: # \"Raw('INJECTED')\"\n\nbody\n"


def test_markdown_eval_comment_not_run_when_untrusted():
    out = _tex(_MD_EVAL, InputKind.MARKDOWN, TrustLevel.UNTRUSTED)
    assert b"INJECTED" not in out


def test_markdown_eval_comment_not_run_when_sandboxed():
    out = _tex(_MD_EVAL, InputKind.MARKDOWN, TrustLevel.SANDBOXED)
    assert b"INJECTED" not in out


def test_markdown_eval_comment_runs_when_trusted():
    out = _tex(_MD_EVAL, InputKind.MARKDOWN, TrustLevel.TRUSTED)
    assert b"INJECTED" in out


# -- exec vector 3: .tex pytex(...) replacements ---------------------------

_TEX_REPL = rb"\iffalse{pytex('AA' + 'BB')}\fi tail"


def test_tex_replacement_inert_when_untrusted():
    out = _tex(_TEX_REPL, InputKind.TEX, TrustLevel.UNTRUSTED)
    assert b"AABB" not in out
    assert b"pytex" in out  # preserved as a literal


def test_tex_replacement_evaluated_when_trusted():
    out = _tex(_TEX_REPL, InputKind.TEX, TrustLevel.TRUSTED)
    assert b"AABB" in out


# -- exec vector 4: dangerous packages / shell-escape surface --------------


def test_minted_package_rejected_for_untrusted():
    with pytest.raises(TrustError, match="code-execution"):
        _tex(rb"\usepackage{minted}\section{x}", InputKind.TEX, TrustLevel.UNTRUSTED)


def test_shellesc_package_rejected_for_untrusted():
    with pytest.raises(TrustError):
        _tex(rb"\usepackage{shellesc}", InputKind.TEX, TrustLevel.UNTRUSTED)


def test_unknown_package_rejected_for_untrusted():
    with pytest.raises(TrustError, match="allowlist"):
        _tex(rb"\usepackage{totally-unknown}", InputKind.TEX, TrustLevel.UNTRUSTED)


def test_safe_package_allowed_for_untrusted():
    out = _tex(rb"\usepackage{amsmath}\section{x}", InputKind.TEX, TrustLevel.UNTRUSTED)
    assert b"amsmath" in out


# -- size limits -----------------------------------------------------------


def test_oversize_input_rejected():
    limits = BuildLimits(max_input_bytes=8)
    with pytest.raises(LimitError, match="input"):
        render_blob(
            BuildRequest(
                source=b"x" * 64,
                input_kind=InputKind.TEX,
                output_kind=OutputKind.TEX,
                trust=TrustLevel.TRUSTED,
                limits=limits,
            )
        )


def test_oversize_output_rejected():
    limits = BuildLimits(max_output_bytes=4)
    with pytest.raises(LimitError, match="output"):
        render_blob(
            BuildRequest(
                source=rb"\section{a long enough heading}",
                input_kind=InputKind.TEX,
                output_kind=OutputKind.TEX,
                trust=TrustLevel.TRUSTED,
                limits=limits,
            )
        )


# -- asset name validation through the public API --------------------------


def test_unsafe_asset_name_rejected_at_request():
    with pytest.raises(TrustError):
        render_blob(
            BuildRequest(
                source=rb"\section{x}",
                input_kind=InputKind.TEX,
                output_kind=OutputKind.TEX,
                trust=TrustLevel.UNTRUSTED,
                assets={"../escape.png": b"data"},
            )
        )


# -- malformed input -------------------------------------------------------


def test_non_utf8_source_raises_api_error():
    with pytest.raises(ApiError, match="UTF-8"):
        _tex(b"\xff\xfe\x00bad", InputKind.TEX, TrustLevel.UNTRUSTED)


# -- malformed source -> typed CompileError (Red-Team O1-O3) ----------------
#
# A broken document must surface as a CompileError (an ApiError), never a bare
# Exception forcing a blanket 500. The message must stay generic: no temp path,
# no stacktrace leaked to the caller.


def _expect_clean_compile_error(
    source: bytes, kind: InputKind, trust: TrustLevel
) -> None:
    with pytest.raises(CompileError) as exc_info:
        _tex(source, kind, trust)
    msg = str(exc_info.value)
    assert "/tmp" not in msg
    assert "input.py" not in msg
    assert "Traceback" not in msg


def test_python_syntax_error_becomes_compile_error(tmp_path, monkeypatch):
    # O1: a Python SyntaxError in .tex.py source.
    monkeypatch.chdir(tmp_path)
    _expect_clean_compile_error(
        b"def (:\n    pass\n", InputKind.TEX_PY, TrustLevel.TRUSTED
    )


def test_non_node_pytex_becomes_compile_error(tmp_path, monkeypatch):
    # O2: __pytex__ is not a TeX node.
    monkeypatch.chdir(tmp_path)
    _expect_clean_compile_error(
        b"__pytex__ = 42\n", InputKind.TEX_PY, TrustLevel.TRUSTED
    )


def test_missing_pytex_var_becomes_compile_error(tmp_path, monkeypatch):
    # O2: module defines no __pytex__ at all.
    monkeypatch.chdir(tmp_path)
    _expect_clean_compile_error(b"x = 1\n", InputKind.TEX_PY, TrustLevel.TRUSTED)


def test_eval_error_in_tex_replacement_becomes_compile_error():
    # O3: a pytex(...) replacement that raises while being eval'd.
    _expect_clean_compile_error(
        rb"\iffalse{pytex(1 / 0)}\fi", InputKind.TEX, TrustLevel.TRUSTED
    )


def test_typed_errors_still_propagate_unchanged():
    # The wrapper must not swallow our own ApiError subclasses into CompileError.
    with pytest.raises(TrustError):
        _tex(rb"\usepackage{minted}", InputKind.TEX, TrustLevel.UNTRUSTED)


# -- async isolation (the Part 1 <-> Part 2 link) --------------------------

# Nested callouts -> nested ColoredBox -> exercises the _render_depth ContextVar.
_NESTED_BOXES = (
    b"> [!NOTE]\n> outer\n>\n> > [!WARNING]\n> > middle\n> >\n"
    b"> > > [!TIP]\n> > > inner\n"
)


def test_concurrent_async_renders_are_isolated():
    reference = _tex(_NESTED_BOXES, InputKind.MARKDOWN, TrustLevel.TRUSTED)

    async def _run() -> list[bytes]:
        reqs = [
            BuildRequest(
                source=_NESTED_BOXES,
                input_kind=InputKind.MARKDOWN,
                output_kind=OutputKind.TEX,
                trust=TrustLevel.TRUSTED,
            )
            for _ in range(32)
        ]
        results = await asyncio.gather(*(render_blob_async(r) for r in reqs))
        return [r.output for r in results]

    outputs = asyncio.run(_run())
    # Every concurrent render must match the single-threaded reference: if the
    # depth ContextVar leaked across tasks, box opacities would diverge.
    assert all(out == reference for out in outputs)


def test_markdown_report_variant_materialises_inline_fonts(tmp_path):
    """Report/protocol variants embed ``Path=fonts/...``; the bundled TTFs must be
    written into the compile workdir, or XeTeX cannot find e.g. ``Blender-Medium``."""
    from pytex_api._policy import policy_for
    from pytex_api._render import _render_markdown_source

    req = BuildRequest(
        source=b"---\ntyp: protokoll\ngremium: stupa\ntitle: T\n---\n\n# H\n\nx\n",
        input_kind=InputKind.MARKDOWN,
        output_kind=OutputKind.TEX,
        trust=TrustLevel.TRUSTED,
        variant="protocol-stupa",
    )
    latex = _render_markdown_source(req, policy_for(req.trust), tmp_path)
    written = {p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*.ttf")}
    assert "fonts/Blender/Blender-Medium.ttf" in written
    assert "fonts/Blender/" in latex


def test_markdown_plain_variant_writes_no_fonts(tmp_path):
    """``plain`` documents have no bundled fonts — nothing is written (no-op)."""
    from pytex_api._policy import policy_for
    from pytex_api._render import _render_markdown_source

    req = BuildRequest(
        source=b"# Hi\n\nplain.\n",
        input_kind=InputKind.MARKDOWN,
        output_kind=OutputKind.TEX,
        trust=TrustLevel.UNTRUSTED,
        variant="plain",
    )
    _render_markdown_source(req, policy_for(req.trust), tmp_path)
    assert not list(tmp_path.rglob("*.ttf"))
