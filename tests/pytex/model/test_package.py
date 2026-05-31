from pytex.model.package import DefinePackage, Package


def test_package_basic_render():
    p = Package("xcolor_basic_test")
    assert p.rendered == r"\usepackage{xcolor_basic_test}"


def test_package_with_flag_options():
    p = Package("geometry_test", options={"a4paper"})
    out = p.rendered
    assert out.startswith(r"\usepackage[") and out.endswith("{geometry_test}")
    assert "a4paper" in out


def test_package_with_kv_options():
    p = Package("babel_test", options={("main", "english")})
    assert r"\usepackage[main=english]{babel_test}" == p.rendered


def test_define_package_caches():
    a = DefinePackage("cache_target_test")
    b = DefinePackage("cache_target_test")
    assert a is b


def test_define_package_amends_after():
    base = DefinePackage("amend_after_a_test")
    dep = DefinePackage("amend_after_b_test", after={base})
    assert base in dep.after


def test_package_options_immutable_view():
    p = Package("opt_view_test", options={"x"})
    assert isinstance(p.options, frozenset)
