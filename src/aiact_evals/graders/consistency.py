from aiact_evals.schema import GoldenCase, GradeResult
from aiact_rag.models import Answer


def consistency(en: GoldenCase, cs: GoldenCase, a_en: Answer, a_cs: Answer, min_jaccard: float = 0.5) -> GradeResult:
    """The EN and CS versions of one question should rest on the same Articles."""
    s_en, s_cs = set(a_en.citations), set(a_cs.citations)
    if a_en.refused != a_cs.refused:
        return GradeResult(grader="consistency", passed=False, reason="one language refused, the other answered")
    if not s_en and not s_cs:
        return GradeResult(grader="consistency", passed=True, reason="both cite nothing")
    jaccard = len(s_en & s_cs) / len(s_en | s_cs)
    return GradeResult(
        grader="consistency",
        passed=jaccard >= min_jaccard,
        reason=f"{en.pair_id}: en {sorted(s_en)} vs cs {sorted(s_cs)} (jaccard {jaccard:.2f})",
    )
