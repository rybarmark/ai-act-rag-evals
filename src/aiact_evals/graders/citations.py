from aiact_evals.schema import GoldenCase, GradeResult
from aiact_rag.models import Answer


def citation_validity(case: GoldenCase, answer: Answer) -> GradeResult:
    """Every cited Article must be among the retrieved chunks, and a non-refusal must cite
    something. An answer citing an Article it never saw is an invented citation."""
    if answer.refused:
        return GradeResult(grader="citation_validity", passed=None, reason="answer refused")
    if not answer.citations:
        return GradeResult(grader="citation_validity", passed=False, reason="answer cites nothing")
    invented = [c for c in answer.citations if c not in answer.retrieved_articles]
    return GradeResult(
        grader="citation_validity",
        passed=not invented,
        reason=f"not in retrieved context: {invented}" if invented else "all citations grounded",
    )
