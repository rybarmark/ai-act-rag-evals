from aiact_evals.schema import GoldenCase, GradeResult
from aiact_rag.models import Answer


def refusal(case: GoldenCase, answer: Answer) -> GradeResult:
    """Refuses exactly when it should: out-of-scope questions refused, answerable ones answered."""
    ok = answer.refused == case.should_refuse
    expected = "refuse" if case.should_refuse else "answer"
    actual = "refused" if answer.refused else "answered"
    return GradeResult(grader="refusal", passed=ok, reason=f"expected to {expected}, {actual}")
