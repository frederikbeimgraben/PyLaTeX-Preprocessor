from pytex.commands.builtin import Section
from pytex.model.concat import Concat
from pytex.model.document import Document
from pytex.model.image import IncludeImage


def _pdf(tmp_path, name="x.pdf"):
    p = tmp_path / name
    p.write_bytes(b"%PDF-1.4")
    return p


def test_inline_images_property_collects(tmp_path):
    img = IncludeImage(_pdf(tmp_path), inline_base64=True)
    doc = Document(Concat(Section("s"), img))
    assert len(doc.inline_images) == 1


def test_inline_images_dedupe_same_path(tmp_path):
    p = _pdf(tmp_path)
    doc = Document(
        Concat(
            IncludeImage(p, inline_base64=True),
            IncludeImage(p, inline_base64=True),
        )
    )
    assert len(doc.inline_images) == 1


def test_inline_images_excludes_non_inline(tmp_path):
    p = _pdf(tmp_path)
    doc = Document(
        Concat(
            IncludeImage(p, inline_base64=True),
            IncludeImage(p, inline_base64=False),
        )
    )
    assert len(doc.inline_images) == 1


def test_inline_images_from_preamble(tmp_path):
    p = _pdf(tmp_path)
    doc = Document("body", preamble=IncludeImage(p, inline_base64=True))
    assert len(doc.inline_images) == 1


def test_inline_image_block_empty_returns_empty(tmp_path):
    doc = Document("hi")
    assert doc.inline_image_block.rendered == ""


def test_inline_image_block_renders(tmp_path):
    p = _pdf(tmp_path)
    doc = Document(IncludeImage(p, inline_base64=True))
    block = doc.inline_image_block.rendered
    assert "filecontents*" in block
    assert p.as_posix() + ".b64" in block


def test_write_inline_images_creates_files(tmp_path):
    p = _pdf(tmp_path, "src.pdf")
    out_dir = tmp_path / "out"
    doc = Document(IncludeImage(p, inline_base64=True))
    written = doc.write_inline_images(str(out_dir))
    assert len(written) == 1
    from pathlib import Path

    assert Path(written[0]).exists()
    assert Path(written[0]).read_bytes() == p.read_bytes()


def test_rendered_emits_filecontents_before_document(tmp_path):
    p = _pdf(tmp_path)
    out = Document(IncludeImage(p, inline_base64=True)).rendered
    fc = out.find(r"\begin{filecontents*}")
    doc = out.find(r"\begin{document}")
    assert 0 <= fc < doc
