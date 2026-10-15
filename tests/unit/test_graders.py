import json

from conftest import make_answer

from aiact_evals.graders import LLMJudge, citation_validity, consistency, refusal, retrieval_hit
from aiact_evals.graders.judge import parse_verdict
from aiact_evals.schema import GoldenCase
from aiact_rag.llm import FakeLLM

ANSWERABLE = GoldenCase(id="c1", category="factual", lang="en", question="q",
                        expected_articles=["Art. 99"], reference_answer="r")
OOS = GoldenCase(id="c2", category="out_of_scope", lang="en", question="q", should_refuse=True)


def test_retrieval_hit():
    assert retrieval_hit(ANSWERABLE, make_answer(retrieved=["5", "99"])).passed is True
    assert retrieval_hit(ANSWERABLE, make_answer(retrieved=["5"])).passed is False
    assert retrieval_hit(OOS, make_answer()).passed is None


def test_citation_validity_catches_invented_citation():
    assert citation_validity(ANSWERABLE, make_answer(citations=["99"], retrieved=["99"])).passed is True
    bad = citation_validity(ANSWERABLE, make_answer(citations=["99", "250"], retrieved=["99"]))
    assert bad.passed is False and "250" in bad.reason
    assert citation_validity(ANSWERABLE, make_answer(citations=[])).passed is False
    assert citation_validity(ANSWERABLE, make_answer(refused=True)).passed is None


def test_refusal():
    assert refusal(OOS, make_answer(refused=True)).passed is True
    assert refusal(OOS, make_answer(refused=False)).passed is False
    assert refusal(ANSWERABLE, make_answer(refused=True)).passed is False


def test_consistency():
    en = GoldenCase(id="e", category="factual", lang="en", question="q", expected_articles=["99"],
                    reference_answer="r", pair_id="p")
    cs = en.model_copy(update={"id": "c", "lang": "cs"})
    same = consistency(en, cs, make_answer(citations=["99"]), make_answer(citations=["99"], lang="cs"))
    diff = consistency(en, cs, make_answer(citations=["99"]), make_answer(citations=["5"], lang="cs"))
    assert same.passed is True and diff.passed is False


def test_parse_verdict():
    assert parse_verdict('{"verdict": "pass", "reason": "ok"}') == (True, "ok")
    assert parse_verdict('Sure! {"verdict": "FAIL", "reason": "x"}')[0] is False
    assert parse_verdict("I think it passes")[0] is None


def test_judge_uses_llm_and_skips_refusals():
    llm = FakeLLM(json.dumps({"verdict": "fail", "reason": "wrong amount"}))
    judge = LLMJudge(llm)
    g = judge.correctness(ANSWERABLE, make_answer(text="EUR 10 million [Art. 99]", citations=["99"]))
    assert g.passed is False and g.reason == "wrong amount"
    assert judge.faithfulness(ANSWERABLE, make_answer(refused=True)).passed is None
    assert len(llm.calls) == 1
