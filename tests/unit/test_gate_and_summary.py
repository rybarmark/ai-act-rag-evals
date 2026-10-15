from conftest import make_answer

from aiact_evals.calibration import cohen_kappa
from aiact_evals.gate import check
from aiact_evals.runner import summarize
from aiact_evals.schema import CaseRun, GoldenCase, GradeResult


def _summary(rate):
    return {"graders": {"faithfulness": {"passed": 0, "total": 0, "rate": rate}}}


def test_gate_threshold_and_baseline():
    t = {"faithfulness": 0.9}
    assert check(_summary(0.95), t) == []
    assert "below threshold" in check(_summary(0.85), t)[0]
    problems = check(_summary(0.91), t, baseline=_summary(0.98), max_drop_pp=3)
    assert len(problems) == 1 and "dropped" in problems[0]
    assert check(_summary(None), t) == []


def test_summary_rates_and_flaky():
    case = GoldenCase(id="c1", category="factual", lang="en", question="q",
                      expected_articles=["99"], reference_answer="r")
    runs = [
        CaseRun(case_id="c1", run=0, answer=make_answer(), grades=[GradeResult(grader="faithfulness", passed=True)]),
        CaseRun(case_id="c1", run=1, answer=make_answer(), grades=[GradeResult(grader="faithfulness", passed=False)]),
        CaseRun(case_id="c1", run=2, answer=make_answer(), grades=[GradeResult(grader="retrieval_hit", passed=None)]),
    ]
    s = summarize([case], runs)
    assert s["graders"]["faithfulness"] == {"passed": 1, "total": 2, "rate": 0.5}
    assert "retrieval_hit" not in s["graders"]
    assert s["flaky"] == ["c1 [faithfulness]"]
    assert len(s["failures"]) == 1


def test_cohen_kappa():
    assert cohen_kappa([True, True, False, False], [True, False, False, False]) == 0.5
    assert cohen_kappa([True, False], [True, False]) == 1.0
