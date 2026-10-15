# ai-act-rag-evals

**A small question-answering assistant over the EU AI Act, and the test suite that measures how good its answers are and blocks any change that makes them worse.**

The assistant is deliberately simple. The point of this repo is the evaluation: how you prove that a probabilistic LLM system is good enough, and keep it that way when prompts, models or documents change.

> Not legal advice. The assistant is a test subject.

## What the eval suite checks

| Grader | Type | Question it answers |
| --- | --- | --- |
| `retrieval_hit` | deterministic | Did retrieval surface an expected Article in the top-k? |
| `citation_validity` | deterministic | Does every Article the answer cites exist in what it retrieved? (catches invented citations) |
| `refusal` | deterministic | Does it decline questions the Act doesn't answer, and answer those it does? |
| `faithfulness` | LLM judge | Is every claim supported by the retrieved text? |
| `correctness` | LLM judge | Does it match an expert reference answer on the key facts? |
| `consistency` | deterministic | Do the English and Czech versions of a question cite the same Articles? |

Plus: every case runs 3 times to expose **flaky** answers, the LLM judge is **calibrated** against hand labels (Cohen's kappa), and CI **fails** if any score drops below its threshold or more than 3 points below the baseline.

## How it works

```
EUR-Lex HTML (EN + CS) -> parse by Article -> embed (multilingual-e5-small) -> NumPy index
question -> retrieve top-k -> LLM answers with [Art. N] citations -> Answer
golden set -> pipeline -> graders (x3 runs) -> results JSON -> gate + HTML report
```

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[embed,dev]"
cp .env.example .env            # add ANTHROPIC_API_KEY

aiact fetch                     # EN + CS XHTML from the EU Publications Office (CELLAR)
aiact parse                     # -> data/processed/chunks.jsonl (commit it)
aiact build-index
aiact ask "What is the maximum fine for prohibited AI practices?"
aiact ask "Jaká je maximální pokuta za zakázané praktiky?" --lang cs

python -m pytest                          # unit tests, free
python -m aiact_evals.run --mode smoke    # ~20 cases, 1 run
python -m aiact_evals.run --mode full     # all cases, 3 runs
python -m aiact_evals.gate results/latest.json
open results/report.html
```

## Repo layout

```
config/settings.yaml        every knob the system depends on (models, top_k, thresholds)
src/aiact_rag/              the system under test: ingest, index, prompts, pipeline, CLI
src/aiact_evals/            the harness: schema, dataset, graders, runner, gate, report, calibration
data/golden/                golden cases (JSONL) + schema docs
data/calibration/           hand labels for judge calibration
tests/unit/                 free, deterministic tests (fake LLM, hash embedder)
tests/evals/                live per-case checks: pytest -m eval
.github/workflows/          ci.yml (every push), eval.yml (PR smoke, nightly full)
```

CI holds no API key. `eval.yml` authenticates with [Workload Identity Federation](https://platform.claude.com/docs/en/manage-claude/wif-providers/github-actions): GitHub issues a short-lived OIDC token, the Anthropic SDK exchanges it, and the federation rule only trusts runs on `main`. The rule, organisation, service account and workspace IDs are repo variables, not secrets. Locally, use an API key in `.env`.

## Results

_Baseline table goes here after the first full run._

## The regression story

_Phase 6: a change that looked fine (a cheaper model / a "cleaner" prompt / an amended corpus), and the suite catching it._

## Corpus version

The AI Act was amended by the AI Omnibus (formally adopted 2026). `corpus.version` in `config/settings.yaml` records which text is indexed, and is written into every result file. Cases whose answer depends on the version are marked `version_sensitive`.

## License

MIT
