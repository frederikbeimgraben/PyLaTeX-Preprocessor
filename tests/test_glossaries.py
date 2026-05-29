"""Tests for the glossaries library."""

from pytex import (
    Acronyms,
    AcronymEntry,
    Glossary,
    GlossaryEntry,
    MakeGlossaries,
    PrintGlossary,
    acr,
    acrfull,
    gls,
    glspl,
)


class TestEntries:
    def test_glossary_entry_basic(self):
        out = GlossaryEntry("tk", "Textkörper", "Der Bereich der Arbeit").serialize()
        assert out.startswith("\\newglossaryentry{tk}{")
        assert "name={Textkörper}" in out
        assert "description={Der Bereich der Arbeit}" in out

    def test_glossary_entry_german_keys(self):
        out = GlossaryEntry(
            "tk", "Textkörper", "x", genitive="Textkörpers", plural="Textkörper"
        ).serialize()
        assert "genitive={Textkörpers}" in out
        assert "plural={Textkörper}" in out

    def test_description_not_space_escaped(self):
        out = GlossaryEntry("k", "N", "two words").serialize()
        assert "two words" in out
        assert "two~words" not in out

    def test_acronym_entry(self):
        assert (
            AcronymEntry("MPG", "MPG", "Medizinproduktegesetz").serialize()
            == "\\newacronym{MPG}{MPG}{Medizinproduktegesetz}"
        )

    def test_acronym_with_description(self):
        out = AcronymEntry("a", "A", "Alpha", description="first").serialize()
        assert out.startswith("\\newacronym[description={first}]{a}")

    def test_required_packages(self):
        assert GlossaryEntry("k", "n", "d").required_packages == {"glossaries"}


class TestContainers:
    def test_glossary_children_and_serialize(self):
        e1 = GlossaryEntry("a", "A", "x")
        e2 = GlossaryEntry("b", "B", "y")
        g = Glossary(e1, e2)
        assert g.children == (e1, e2)
        assert g.serialize() == e1.serialize() + "\n" + e2.serialize()

    def test_acronyms_is_glossary(self):
        a = Acronyms(AcronymEntry("MPG", "MPG", "Medizinproduktegesetz"))
        assert isinstance(a, Glossary)
        assert "\\newacronym" in a.serialize()


class TestReferences:
    def test_gls_default(self):
        assert gls("k").serialize() == "\\gls{k}"

    def test_gls_case(self):
        assert gls("k", case="capitalized").serialize() == "\\Gls{k}"
        assert gls("k", case="upper").serialize() == "\\GLS{k}"

    def test_gls_long(self):
        assert gls("k", format="long").serialize() == "\\glslong{k}"

    def test_gls_full_is_acrfull(self):
        assert gls("k", format="full").serialize() == "\\acrfull{k}"

    def test_glspl(self):
        assert glspl("k").serialize() == "\\glspl{k}"

    def test_acr_and_acrfull(self):
        assert acr("MPG").serialize() == "\\acrshort{MPG}"
        assert acrfull("MPG").serialize() == "\\acrfull{MPG}"


class TestControls:
    def test_make_glossaries(self):
        assert MakeGlossaries.serialize() == "\\makeglossaries"

    def test_print_glossary(self):
        assert PrintGlossary().serialize() == "\\printglossary"
        assert (
            PrintGlossary(type="acronym", title="Abk").serialize()
            == "\\printglossary[type=acronym,title=Abk]"
        )
