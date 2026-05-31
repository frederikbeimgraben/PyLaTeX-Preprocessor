import base64

import pytest

from pytex.model.concat import Concat
from pytex.model.document import Document
from pytex.model.image import (
    IncludeImage,
    collect_inline_images,
    filecontents_b64_block,
)


@pytest.fixture
def pdf_file(tmp_path):
    p = tmp_path / "fake.pdf"
    p.write_bytes(b"%PDF-1.4 not really a pdf")
    return p


def test_renders_includegraphics(pdf_file):
    out = IncludeImage(pdf_file).rendered
    assert "includegraphics" in out and pdf_file.as_posix() in out


def test_options_render(pdf_file):
    out = IncludeImage(pdf_file, width="5cm", keepaspectratio=True).rendered
    assert "[width=5cm,keepaspectratio]" in out


def test_collect_inline_images_filters(pdf_file):
    a = IncludeImage(pdf_file, inline_base64=True)
    b = IncludeImage(pdf_file, inline_base64=False)
    tree = Concat(a, b)
    found = collect_inline_images(tree)
    assert found == (a,)


def test_collect_dedupes_same_path(pdf_file):
    a = IncludeImage(pdf_file, inline_base64=True)
    b = IncludeImage(pdf_file, inline_base64=True)
    tree = Concat(a, b)
    found = collect_inline_images(tree)
    assert len(found) == 1


def test_filecontents_block_contains_base64(pdf_file):
    img = IncludeImage(pdf_file, inline_base64=True)
    block = filecontents_b64_block(img)
    assert "begin{filecontents*}" in block
    assert pdf_file.as_posix() + ".b64" in block
    payload = base64.b64encode(pdf_file.read_bytes()).decode("ascii")
    assert payload[:20] in block


def test_unsupported_extension_raises(tmp_path):
    p = tmp_path / "x.gif"
    p.write_bytes(b"GIF89a")
    img = IncludeImage(p)
    with pytest.raises(ValueError):
        _ = img.resolved_path


def test_document_emits_filecontents_block(pdf_file):
    img = IncludeImage(pdf_file, inline_base64=True)
    doc = Document(img)
    out = doc.rendered
    assert "begin{filecontents*}" in out
    assert pdf_file.as_posix() + ".b64" in out


def test_document_no_block_without_inline(pdf_file):
    img = IncludeImage(pdf_file, inline_base64=False)
    out = Document(img).rendered
    assert "filecontents*" not in out
