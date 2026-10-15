# CLAUDE.md

Guidance for Claude Code when working in this repo.

## What this project is

A small RAG assistant over the EU AI Act (Regulation (EU) 2024/1689, EN + CS), and an
eval suite that measures and gates its answer quality. **The assistant is the system under
test; the eval suite is the product.** It is a public portfolio piece for AI QA / LLM
evaluation work, so code clarity and honest measurement matter more than features.

## Commands

```bash
pip install -e ".[embed,dev]"              # embed = sentence-transformers (pulls torch)
python -m pytest                           # unit tests: free, no API, no model download
python -m pytest -m eval                   # live per-case checks: needs ANTHROPIC_API_KEY + built index
ruff check .                               # lint (line length 100)

aiact fetch | parse | build-index          # corpus -> data/processed/chunks.jsonl -> index.npz
aiact ask "question" [--lang cs]

python -m aiact_evals.run --mode smoke     # ~20 cases, 1 run
python -m aiact_evals.run --mode full      # all cases, settings.eval.repeats runs
python -m aiact_evals.run --no-judge       # deterministic graders only
python -m aiact_evals.gate results/latest.json [--update-baseline]
python -m aiact_evals.calibration results/latest.json
```

Use `python -m pytest`, not bare `pytest`, so the project's interpreter is used.

## Layout

- `config/settings.yaml`: every knob (models, top_k, corpus version, thresholds). Loaded via `aiact_rag.config.load_settings()`; resolve repo-relative paths with `Settings.path()`.
- `src/aiact_rag/`: system under test. `ingest/` (fetch, parse, chunk), `index.py`, `llm.py`, `prompts.py`, `pipeline.py`, `refs.py`, `cli.py`.
- `src/aiact_evals/`: harness. `schema.py`, `dataset.py`, `graders/`, `runner.py`, `gate.py`, `report.py`, `calibration.py`, `run.py`.
- `data/golden/*.jsonl`: golden cases (schema in `data/golden/README.md`).
- `tests/unit/`: deterministic tests using `FakeLLM` and the `HashEmbedder` in `tests/conftest.py`.
- `tests/evals/`: live tests, marked `eval`, deselected by default.

## Rules

**Measurement integrity. These matter most.**
- Never lower a threshold, edit `results/baseline.json`, loosen a grader or delete a golden case to make a run pass. If a score drops, report it and investigate. Changing a threshold or the baseline is the user's decision; ask first.
- Never write or change a `reference_answer` or `expected_articles` from memory. Check it against the Article text in `data/processed/chunks.jsonl` (or EUR-Lex) and quote the paragraph you relied on in your reply.
- Any real failure you find gets a new golden case, so it can't regress silently.
- A grader that can't decide returns `passed=None` (not applicable / unparseable). Never default to pass or fail.

**Code.**
- Unit tests must never call a real API or download a model. Use `FakeLLM` and `HashEmbedder`.
- Every new grader gets unit tests covering pass, fail and not-applicable.
- Article references are always normalised with `aiact_rag.refs.normalise_ref`: `"5"`, `"Annex III"`. Display form (`"Art. 5"`) only via `display_ref`.
- Prompts live in `prompts.py` and `graders/judge.py`. Treat a prompt change like a code change: run at least the smoke eval and state the score change in the PR.
- Model names, top_k and similar values come from `settings.yaml`, never hard-coded.
- Keep dependencies minimal. Don't add a vector database, LangChain or an eval framework without asking; the plain implementation is intentional and part of the portfolio's point.
- Python 3.11+, type hints, pydantic models for data crossing module boundaries.

**Corpus.**
- `corpus.version` in `settings.yaml` must change whenever the indexed text changes. The AI Act was amended by the AI Omnibus (2026); cases whose answer depends on the version are marked `version_sensitive: true`.
- `data/processed/chunks.jsonl` is committed (CI builds the index from it). Re-run `aiact parse` and commit it when the corpus changes. `index.npz` and `data/raw/` are not committed.
- The parser relies on EUR-Lex `div id="art_N"` / `"anx_N"` markup. After parsing, check the counts: 113 Articles per language for the original text.

**Cost.**
- Live evals cost money. Prefer `--mode smoke` or `--no-judge` while iterating, and say before running a full eval.
- Never commit `.env` or print the API key.

## Before finishing a change

1. `ruff check .` and `python -m pytest` pass.
2. If `src/`, prompts, config or golden data changed: run the smoke eval (when a key and index are available) and report per-grader scores against the baseline.
3. Update `README.md` if commands, graders or layout changed.
