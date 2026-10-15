"""How far can the LLM judge be trusted? Compare its verdicts with hand labels.

data/calibration/labels.jsonl, one line per hand-labelled grade:
    {"case_id": "en-fact-001", "grader": "faithfulness", "human_pass": true}

    python -m aiact_evals.calibration results/latest.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def agreement(a: list[bool], b: list[bool]) -> float:
    return sum(x == y for x, y in zip(a, b, strict=True)) / len(a)


def cohen_kappa(a: list[bool], b: list[bool]) -> float:
    """Agreement corrected for chance. ~0.7+ is usable; below that, fix the judge prompt."""
    n = len(a)
    po = agreement(a, b)
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("results", type=Path)
    p.add_argument("--labels", type=Path, default=Path("data/calibration/labels.jsonl"))
    args = p.parse_args()
    labels = [json.loads(x) for x in args.labels.read_text(encoding="utf-8").splitlines() if x.strip()]
    runs = json.loads(args.results.read_text(encoding="utf-8"))["runs"]
    judged = {
        (r["case_id"], g["grader"]): g["passed"]
        for r in runs
        if r["run"] == 0
        for g in r["grades"]
    }
    for grader in sorted({x["grader"] for x in labels}):
        pairs = [
            (x["human_pass"], judged[(x["case_id"], grader)])
            for x in labels
            if x["grader"] == grader and judged.get((x["case_id"], grader)) is not None
        ]
        if not pairs:
            continue
        human, judge = [h for h, _ in pairs], [j for _, j in pairs]
        print(f"{grader:<14} n={len(pairs):<3} agreement {agreement(human, judge):.0%}  kappa {cohen_kappa(human, judge):.2f}")


if __name__ == "__main__":
    main()
