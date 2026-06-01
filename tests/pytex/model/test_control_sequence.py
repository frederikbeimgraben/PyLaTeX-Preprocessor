from pytex.model.control_sequence import ControlSequence, Parameter
from pytex.model.raw import Raw
from pytex.packages import AMSMATH


def test_parameter_string_required():
    assert Parameter("x").rendered == "{x}"


def test_parameter_string_optional():
    assert Parameter("x", optional=True).rendered == "[x]"


def test_parameter_tex_value():
    assert Parameter(Raw("foo")).rendered == "{foo}"


def test_parameter_dict_value():
    out = Parameter({"a": "1", "b": "2"}).rendered
    assert out.startswith("{") and out.endswith("}")
    assert "a=1" in out and "b=2" in out


def test_control_sequence_no_params():
    assert ControlSequence("hfill", ()).rendered == r"\hfill"


def test_control_sequence_one_param():
    assert ControlSequence("textbf", (Parameter("x"),)).rendered == r"\textbf{x}"


def test_control_sequence_multi_params():
    cs = ControlSequence("frac", (Parameter("1"), Parameter("2")))
    assert cs.rendered == r"\frac{1}{2}"


def test_control_sequence_mixed_optional():
    cs = ControlSequence(
        "sqrt",
        (Parameter("3", optional=True), Parameter("x")),
    )
    assert cs.rendered == r"\sqrt[3]{x}"


def test_required_packages_default_empty():
    cs = ControlSequence("x", ())
    assert cs.requires == frozenset()


def test_required_packages_attached():
    cs = ControlSequence("x", (), required_packages=frozenset({AMSMATH}))
    assert cs.requires == frozenset({AMSMATH})
