from pytex.helpers.coerce import coerce_tex
from pytex.interface.tex import TeX
from pytex.model.raw import Raw


def test_coerce_str_to_raw():
    out = coerce_tex("hello")
    assert isinstance(out, Raw)
    assert out.rendered == "hello"


def test_coerce_tex_passthrough():
    r = Raw("x")
    assert coerce_tex(r) is r


def test_coerced_tex_protocol_check():
    assert isinstance(coerce_tex("x"), TeX)
