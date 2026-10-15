"""Live checks against the real pipeline. Costs API calls: run with `pytest -m eval`.

The aggregate gate (python -m aiact_evals.run + gate) is the real quality check; this file
gives per-case failures in familiar pytest output while you work on the system.
"""

import os

import pytest

from aiact_evals.dataset import load_cases, select_smoke
from aiact_evals.graders import DETERMINISTIC
from aiact_rag.config import load_settings

pytestmark = pytest.mark.eval

_s = load_settings()
_CASES = select_smoke(load_cases([_s.path(f) for f in _s.eval.golden_files]), _s.eval.smoke_size)


@pytest.fixture(scope="module")
def pipeline():
    # API key locally, Workload Identity Federation in CI (see .github/workflows/eval.yml).
    if not (
        os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_FEDERATION_RULE_ID")
    ):
        pytest.skip("no Anthropic credentials: set ANTHROPIC_API_KEY or the federation env vars")
    if not _s.path(_s.corpus.index_path).exists():
        pytest.skip("index not built: run `aiact parse` and `aiact build-index`")
    from aiact_rag.pipeline import RagPipeline

    return RagPipeline.from_settings(_s)


@pytest.mark.parametrize("case", _CASES, ids=[c.id for c in _CASES])
def test_deterministic_graders(case, pipeline):
    answer = pipeline.answer(case.question, case.lang)
    failed = [g for g in (grader(case, answer) for grader in DETERMINISTIC) if g.passed is False]
    assert not failed, "; ".join(f"{g.grader}: {g.reason}" for g in failed) + f"\n---\n{answer.text}"
