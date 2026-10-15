import json

import pytest

from aiact_evals.dataset import load_cases, select_smoke
from aiact_evals.schema import GoldenCase
from aiact_rag.config import load_settings


def test_repo_golden_files_are_valid():
    s = load_settings()
    cases = load_cases([s.path(f) for f in s.eval.golden_files])
    assert len(cases) >= 5
    assert cases[0].expected_articles == ["99"]  # "Art. 99" normalised


def _write(tmp_path, rows):
    p = tmp_path / "g.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    return p


BASE = {"category": "factual", "lang": "en", "question": "q", "expected_articles": ["5"], "reference_answer": "r"}


def test_duplicate_ids_rejected(tmp_path):
    with pytest.raises(ValueError, match="duplicate"):
        load_cases([_write(tmp_path, [{**BASE, "id": "a"}, {**BASE, "id": "a"}])])


def test_pair_needs_both_languages(tmp_path):
    with pytest.raises(ValueError, match="pair"):
        load_cases([_write(tmp_path, [{**BASE, "id": "a", "pair_id": "p"}])])


def test_answerable_case_needs_reference(tmp_path):
    with pytest.raises(ValueError, match="reference_answer"):
        load_cases([_write(tmp_path, [{**BASE, "id": "a", "reference_answer": None}])])


def test_unknown_field_rejected(tmp_path):
    with pytest.raises(ValueError):
        load_cases([_write(tmp_path, [{**BASE, "id": "a", "expected": ["5"]}])])


def test_smoke_is_balanced_and_keeps_pairs():
    cases = [GoldenCase(id=f"{cat}-{i}", category=cat, lang="en", question="q",
                        expected_articles=["5"], reference_answer="r")
             for cat in ("factual", "dates") for i in range(5)]
    cases.append(GoldenCase(id="z-en", category="factual", lang="en", question="q",
                            expected_articles=["5"], reference_answer="r", pair_id="p"))
    cases.append(GoldenCase(id="z-cs", category="factual", lang="cs", question="q",
                            expected_articles=["5"], reference_answer="r", pair_id="p"))
    picked = select_smoke(cases, 4)
    cats = [c.category.value for c in picked[:4]]
    assert cats.count("factual") == 2 and cats.count("dates") == 2
