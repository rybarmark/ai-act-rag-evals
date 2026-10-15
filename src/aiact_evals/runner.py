"""Run golden cases through the pipeline, grade them, and summarise."""

from __future__ import annotations

from collections import defaultdict

from aiact_evals.graders import DETERMINISTIC, LLMJudge, consistency
from aiact_evals.schema import CaseRun, GoldenCase, GradeResult
from aiact_rag.models import Answer


class Answerer:  # anything with .answer(question, lang) -> Answer, e.g. RagPipeline
    def answer(self, question: str, lang: str) -> Answer: ...


def run_cases(
    cases: list[GoldenCase], pipeline: Answerer, judge: LLMJudge | None, repeats: int = 1
) -> list[CaseRun]:
    runs: list[CaseRun] = []
    for run in range(repeats):
        for case in cases:
            answer = pipeline.answer(case.question, case.lang)
            grades = [g(case, answer) for g in DETERMINISTIC]
            if judge:
                grades += [judge.faithfulness(case, answer), judge.correctness(case, answer)]
            runs.append(CaseRun(case_id=case.id, run=run, answer=answer, grades=grades))
            print(f"  run {run + 1}/{repeats}  {case.id:<28} " + " ".join(_mark(g) for g in grades))
    return runs


def _mark(g: GradeResult) -> str:
    return {True: ".", False: "F", None: "-"}[g.passed]


def pair_consistency(cases: list[GoldenCase], runs: list[CaseRun]) -> list[GradeResult]:
    by_id = {c.id: c for c in cases}
    answers = {(r.case_id, r.run): r.answer for r in runs}
    pairs: dict[str, dict[str, GoldenCase]] = defaultdict(dict)
    for c in cases:
        if c.pair_id:
            pairs[c.pair_id][c.lang] = c
    results = []
    for members in pairs.values():
        en, cs = members.get("en"), members.get("cs")
        if not (en and cs):
            continue
        for run in sorted({r.run for r in runs}):
            a_en, a_cs = answers.get((en.id, run)), answers.get((cs.id, run))
            if a_en and a_cs:
                results.append(consistency(by_id[en.id], by_id[cs.id], a_en, a_cs))
    return results


def summarize(
    cases: list[GoldenCase], runs: list[CaseRun], extra: list[GradeResult] | None = None
) -> dict:
    by_id = {c.id: c for c in cases}
    totals: dict[str, list[int]] = defaultdict(lambda: [0, 0])  # [passed, graded]
    per_case: dict[tuple[str, str], set[bool]] = defaultdict(set)
    failures = []
    for r in runs:
        for g in r.grades:
            if g.passed is None:
                continue
            totals[g.grader][1] += 1
            totals[g.grader][0] += int(g.passed)
            per_case[(r.case_id, g.grader)].add(g.passed)
            if not g.passed:
                failures.append(
                    {
                        "case_id": r.case_id,
                        "run": r.run,
                        "grader": g.grader,
                        "reason": g.reason,
                        "question": by_id[r.case_id].question,
                        "answer": r.answer.text,
                        "retrieved": r.answer.retrieved_articles,
                    }
                )
    for g in extra or []:
        if g.passed is not None:
            totals[g.grader][1] += 1
            totals[g.grader][0] += int(g.passed)
            if not g.passed:
                failures.append({"case_id": "(pair)", "run": None, "grader": g.grader, "reason": g.reason})
    graders = {
        name: {"passed": p, "total": t, "rate": (p / t if t else None)}
        for name, (p, t) in sorted(totals.items())
    }
    flaky = sorted({f"{cid} [{grader}]" for (cid, grader), seen in per_case.items() if len(seen) > 1})
    return {"graders": graders, "flaky": flaky, "failures": failures}
