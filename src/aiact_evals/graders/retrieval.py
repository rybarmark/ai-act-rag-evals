from aiact_evals.schema import GoldenCase, GradeResult
from aiact_rag.models import Answer


def retrieval_hit(case: GoldenCase, answer: Answer) -> GradeResult:
    """Did retrieval surface at least one expected Article in the top-k?"""
    if case.should_refuse:
        return GradeResult(grader="retrieval_hit", passed=None, reason="refusal case")
    got = answer.retrieved_articles
    hit = [a for a in case.expected_articles if a in got]
    return GradeResult(
        grader="retrieval_hit",
        passed=bool(hit),
        reason=f"expected {case.expected_articles}, retrieved {got}",
    )
