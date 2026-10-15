"""LLM-as-judge graders. Their prompts are versioned here and calibrated against
hand labels (see calibration.py) before their scores are trusted."""

from __future__ import annotations

import json
import re

from aiact_evals.schema import GoldenCase, GradeResult
from aiact_rag.llm import LLMClient
from aiact_rag.models import Answer
from aiact_rag.refs import display_ref

FAITHFULNESS_SYSTEM = """You are a strict reviewer checking an answer about the EU AI Act \
against the source excerpts it was given.
Verdict "pass" only if every factual claim in the answer is supported by the excerpts. \
Wording may differ; meaning may not. A claim that adds facts not in the excerpts fails.
Reply with JSON only: {"verdict": "pass" | "fail", "unsupported_claims": [..], "reason": ".."}"""

CORRECTNESS_SYSTEM = """You compare an answer about the EU AI Act with a reference answer \
written by an expert.
Verdict "pass" if the answer contains the key facts of the reference and contradicts none \
of them. Extra correct detail is fine. Missing a key fact, or a wrong number, date or \
Article, fails. The answer may be in Czech or English.
Reply with JSON only: {"verdict": "pass" | "fail", "missing_or_wrong": [..], "reason": ".."}"""

_JSON = re.compile(r"\{.*\}", re.DOTALL)


def parse_verdict(raw: str) -> tuple[bool | None, str]:
    """(passed, reason). Unparseable output -> (None, ...) so it is reported, never
    silently counted as a pass or a fail."""
    m = _JSON.search(raw)
    if not m:
        return None, f"unparseable judge output: {raw[:120]!r}"
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None, f"invalid JSON from judge: {raw[:120]!r}"
    verdict = str(data.get("verdict", "")).lower()
    if verdict not in {"pass", "fail"}:
        return None, f"unknown verdict {verdict!r}"
    return verdict == "pass", str(data.get("reason", ""))


class LLMJudge:
    def __init__(self, llm: LLMClient, *, max_tokens: int = 400, temperature: float = 0.0):
        self.llm = llm
        self.max_tokens = max_tokens
        self.temperature = temperature

    def _ask(self, system: str, user: str) -> tuple[bool | None, str]:
        raw = self.llm.complete(system, user, max_tokens=self.max_tokens, temperature=self.temperature)
        return parse_verdict(raw)

    def faithfulness(self, case: GoldenCase, answer: Answer) -> GradeResult:
        if answer.refused:
            return GradeResult(grader="faithfulness", passed=None, reason="answer refused")
        sources = "\n\n".join(
            f"[{display_ref(r.chunk.article)}]\n{r.chunk.text}" for r in answer.retrieved
        )
        passed, reason = self._ask(
            FAITHFULNESS_SYSTEM,
            f"<excerpts>\n{sources}\n</excerpts>\n\n<answer>\n{answer.text}\n</answer>",
        )
        return GradeResult(grader="faithfulness", passed=passed, reason=reason)

    def correctness(self, case: GoldenCase, answer: Answer) -> GradeResult:
        if case.should_refuse or answer.refused:
            return GradeResult(grader="correctness", passed=None, reason="refusal (graded by refusal)")
        passed, reason = self._ask(
            CORRECTNESS_SYSTEM,
            f"<question>\n{case.question}\n</question>\n\n"
            f"<reference>\n{case.reference_answer}\n</reference>\n\n"
            f"<answer>\n{answer.text}\n</answer>",
        )
        return GradeResult(grader="correctness", passed=passed, reason=reason)
