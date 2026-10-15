"""Run the eval suite.

    python -m aiact_evals.run --mode smoke     # ~20 cases, 1 run (PRs)
    python -m aiact_evals.run --mode full      # all cases, settings.eval.repeats runs
    python -m aiact_evals.run --no-judge       # deterministic graders only (cheaper)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import UTC, datetime

from dotenv import load_dotenv

from aiact_evals.dataset import load_cases, select_smoke
from aiact_evals.graders import LLMJudge
from aiact_evals.report import render_report
from aiact_evals.runner import pair_consistency, run_cases, summarize
from aiact_rag.config import load_settings
from aiact_rag.llm import make_client
from aiact_rag.pipeline import RagPipeline


def _git_sha() -> str:
    if sha := os.environ.get("GITHUB_SHA"):
        return sha[:8]
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def main() -> None:
    load_dotenv()
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["smoke", "full"], default="full")
    p.add_argument("--repeats", type=int)
    p.add_argument("--no-judge", action="store_true")
    args = p.parse_args()

    s = load_settings()
    cases = load_cases([s.path(f) for f in s.eval.golden_files])
    if args.mode == "smoke":
        cases = select_smoke(cases, s.eval.smoke_size)
    repeats = args.repeats or (1 if args.mode == "smoke" else s.eval.repeats)

    pipeline = RagPipeline.from_settings(s)
    judge = None if args.no_judge else LLMJudge(make_client(s.judge), max_tokens=s.judge.max_tokens)
    print(f"{len(cases)} cases x {repeats} runs  (. pass  F fail  - n/a)")
    runs = run_cases(cases, pipeline, judge, repeats)
    summary = summarize(cases, runs, pair_consistency(cases, runs))

    now = datetime.now(UTC)
    results = {
        "meta": {
            "timestamp": now.isoformat(timespec="seconds"),
            "mode": args.mode,
            "cases": len(cases),
            "repeats": repeats,
            "generator": s.generation.model,
            "judge": None if judge is None else s.judge.model,
            "corpus_version": s.corpus.version,
            "top_k": s.retrieval.top_k,
            "git_sha": _git_sha(),
        },
        "summary": summary,
        "runs": [r.model_dump() for r in runs],
    }
    out = s.path(s.eval.results_dir)
    out.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(results, ensure_ascii=False, indent=2)
    (out / f"run-{now:%Y%m%d-%H%M%S}.json").write_text(payload, encoding="utf-8")
    (out / "latest.json").write_text(payload, encoding="utf-8")
    (out / "report.html").write_text(render_report(results, s.eval.thresholds), encoding="utf-8")
    print(f"\nresults -> {out / 'latest.json'}\nreport  -> {out / 'report.html'}")


if __name__ == "__main__":
    main()
