"""Regression gate: exit 1 if a grader is under its threshold or fell too far below
the stored baseline.

    python -m aiact_evals.gate results/latest.json
    python -m aiact_evals.gate results/latest.json --update-baseline
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from aiact_rag.config import load_settings


def check(
    summary: dict, thresholds: dict[str, float], baseline: dict | None = None, max_drop_pp: float = 3.0
) -> list[str]:
    problems = []
    graders = summary["graders"]
    for name, threshold in thresholds.items():
        rate = graders.get(name, {}).get("rate")
        if rate is None:
            continue  # grader had no applicable cases in this run
        if rate < threshold:
            problems.append(f"{name}: {rate:.1%} is below threshold {threshold:.0%}")
        if baseline:
            base = baseline["graders"].get(name, {}).get("rate")
            if base is not None and (base - rate) * 100 > max_drop_pp:
                problems.append(f"{name}: {rate:.1%} dropped {(base - rate) * 100:.1f} pp from baseline {base:.1%}")
    return problems


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("results", type=Path)
    p.add_argument("--update-baseline", action="store_true")
    args = p.parse_args()

    s = load_settings()
    results = json.loads(args.results.read_text(encoding="utf-8"))
    baseline_path = s.path(s.eval.baseline_path)
    baseline = json.loads(baseline_path.read_text(encoding="utf-8")) if baseline_path.exists() else None
    if baseline and baseline["meta"].get("mode") != results["meta"].get("mode"):
        print("note: baseline was a different mode; comparing against thresholds only")
        baseline = None

    problems = check(results["summary"], s.eval.thresholds, baseline, s.eval.max_drop_pp)
    for name, g in results["summary"]["graders"].items():
        rate = "n/a" if g["rate"] is None else f"{g['rate']:.1%}"
        print(f"{name:<20} {rate:>7}  ({g['passed']}/{g['total']})")
    if args.update_baseline:
        shutil.copyfile(args.results, baseline_path)
        print(f"baseline updated -> {baseline_path}")
    if problems:
        print("\nGATE FAILED")
        for line in problems:
            print(f"  - {line}")
        sys.exit(1)
    print("\nGATE PASSED")


if __name__ == "__main__":
    main()
