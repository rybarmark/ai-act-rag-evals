"""Load and validate golden files (JSONL, one case per line)."""

from __future__ import annotations

import json
from collections import defaultdict
from itertools import zip_longest
from pathlib import Path

from aiact_evals.schema import GoldenCase


def load_cases(paths: list[Path]) -> list[GoldenCase]:
    cases: list[GoldenCase] = []
    for path in paths:
        with path.open(encoding="utf-8") as f:
            for n, line in enumerate(f, 1):
                if line.strip():
                    try:
                        cases.append(GoldenCase.model_validate(json.loads(line)))
                    except Exception as e:  # report file and line, then re-raise
                        raise ValueError(f"{path}:{n}: {e}") from e
    _check(cases)
    return cases


def _check(cases: list[GoldenCase]) -> None:
    ids = [c.id for c in cases]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        raise ValueError(f"duplicate case ids: {sorted(dupes)}")
    pairs: dict[str, list[GoldenCase]] = defaultdict(list)
    for c in cases:
        if c.pair_id:
            pairs[c.pair_id].append(c)
    for pid, members in pairs.items():
        if sorted(m.lang for m in members) != ["cs", "en"]:
            raise ValueError(f"pair {pid!r} needs exactly one 'en' and one 'cs' case")


def select_smoke(cases: list[GoldenCase], n: int) -> list[GoldenCase]:
    """Deterministic, category-balanced subset: round-robin over categories, ids sorted.
    Paired cases are kept together so the consistency grader still has data."""
    by_cat: dict[str, list[GoldenCase]] = defaultdict(list)
    for c in sorted(cases, key=lambda c: c.id):
        by_cat[c.category.value].append(c)
    picked: list[GoldenCase] = []
    for row in zip_longest(*by_cat.values()):
        for c in row:
            if c is not None and len(picked) < n:
                picked.append(c)
    picked_ids = {c.id for c in picked}
    pair_ids = {c.pair_id for c in picked if c.pair_id}
    picked += [c for c in cases if c.pair_id in pair_ids and c.id not in picked_ids]
    return picked
