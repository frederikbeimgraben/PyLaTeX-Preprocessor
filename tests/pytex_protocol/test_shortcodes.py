from pytex_protocol.shortcodes import expand_inline_shortcodes, expand_shortcode

META = {
    "gremium": "STUPA",
    "datum": "2026-06-15",
    "anwesend": ["A", "B", "C"],
}


def test_time_shortcode():
    out = expand_shortcode("time 18:30", META).rendered
    assert "18:30" in out
    assert "hanblue" in out  # styled in HSRT blue


def test_field_reference():
    assert expand_shortcode("gremium", META).rendered == "STUPA"


def test_list_reference_joins_with_commas():
    assert expand_shortcode("anwesend", META).rendered == "A, B, C"


def test_count_shortcode():
    assert expand_shortcode("count anwesend", META).rendered == "3"


def test_vote_shortcode_picks_green_when_yes_wins():
    out = expand_shortcode("vote ja=12 nein=3 enthaltung=2", META).rendered
    assert "Ja 12" in out and "Nein 3" in out and "Enthaltung 2" in out
    assert "britishracinggreen" in out


def test_vote_shortcode_red_when_no_wins():
    out = expand_shortcode("vote ja=1 nein=9", META).rendered
    assert "red" in out


def test_unknown_shortcode_is_rendered_verbatim():
    # Escaped braces so the typo is visible in the PDF.
    out = expand_shortcode("nonsense foo", META).rendered
    assert "nonsense foo" in out


def test_inline_split_keeps_surrounding_prose():
    out = expand_inline_shortcodes("Start {{time 9:00}} Ende", META).rendered
    assert out.startswith("Start ")
    assert out.rstrip().endswith("Ende")
    assert "9:00" in out


def test_inline_escapes_prose_specials():
    out = expand_inline_shortcodes("50% & more", META).rendered
    assert r"\%" in out and r"\&" in out
