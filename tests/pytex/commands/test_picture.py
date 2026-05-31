from pytex.commands.picture import Picture, Put


def test_picture_basic():
    out = Picture("10", "5", "body").rendered
    assert out.startswith(r"\begin{picture}(10,5)(0,0)")
    assert out.endswith(r"\end{picture}")
    assert "body" in out


def test_picture_custom_offset():
    out = Picture("10", "5", "x", x_offset="1", y_offset="2").rendered
    assert "(10,5)(1,2)" in out


def test_picture_textwidth():
    out = Picture(r"\textwidth", "0", "x").rendered
    assert r"(\textwidth,0)(0,0)" in out


def test_put_basic():
    out = Put("1", "2", "x").rendered
    assert out == r"\put(1,2){x}"


def test_put_nested_braces_balanced():
    out = Put("0", "0", "ab").rendered
    assert out.count("{") == out.count("}")
