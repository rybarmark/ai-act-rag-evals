import pytest

from aiact_rag.refs import display_ref, extract_citations, normalise_ref


@pytest.mark.parametrize("raw,expected", [
    ("Art. 5", "5"), ("Article 99", "99"), ("5", "5"), ("Čl. 6", "6"), ("článek 50", "50"),
    ("Annex iii", "Annex III"), ("Příloha III", "Annex III"),
])
def test_normalise(raw, expected):
    assert normalise_ref(raw) == expected


def test_normalise_rejects_garbage():
    with pytest.raises(ValueError):
        normalise_ref("Recital 12")


def test_extract_unique_in_order():
    text = "Banned [Art. 5]; see [Annex III] and again [Art. 5]. Czech: [Čl. 6]."
    assert extract_citations(text) == ["5", "Annex III", "6"]


def test_display_ref():
    assert display_ref("5") == "Art. 5"
    assert display_ref("Annex III") == "Annex III"
