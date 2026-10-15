# ai-act-rag-evals – Project Plan

Oct 15, 2026 · @Marek Rybar

Build a small question-answering assistant over the EU AI Act, and around it a test suite that measures how good its answers are and blocks any change that makes them worse. The assistant is the system under test; the eval suite is the portfolio piece.

## Goal

The repo should let a hiring manager or a TWIST-funded team see, in five minutes, that the author can measure and gate the quality of an LLM system.

- **Audience:** companies hiring AI engineers, and teams that need evidence their AI deliverable works.
- **What it proves:** golden datasets, deterministic and LLM-as-judge graders, adversarial testing, repeated runs for flakiness, a CI regression gate, and a readable score report.
- **Why the AI Act:** public, bilingual (EN and CS), and the regulation the high-risk clients care about.
- **Out of scope:** a chat UI, model training, production hosting. The assistant is a Python function and a CLI.

## Architecture

&#91;embedded content: RAG pipeline and eval harness · 12 components\]

The golden set feeds questions into the pipeline. Every answer, with its retrieved chunks, goes to the graders. Their results are compared with thresholds and the stored baseline before a change can merge.

## Tech stack

Python and pytest throughout, so the eval suite reads like ordinary test automation.

| Component | Choice | Why |
| --- | --- | --- |
| Language | Python 3.11+ | Your main stack |
| Source text | Regulation (EU) 2024/1689 from EUR-Lex, EN + CS HTML | Official, free, two language versions of the same text |
| Chunking | One chunk per Article (long Articles split by paragraph) | Every chunk carries its Article number, so retrieval can be graded deterministically |
| Embeddings | sentence-transformers `intfloat/multilingual-e5-small`, run locally | Free, handles Czech, no API cost |
| Vector index | NumPy cosine search, saved to `.npz` | Around 600 chunks needs no database; fully transparent |
| Generator LLM | Anthropic API, small model (configurable) | Cheap per run; the model is a config value, so a model swap is itself a testable change |
| Judge LLM | A stronger model than the generator (configurable) | Judges must be at least as capable as what they grade |
| Test runner | pytest, parametrized over the golden set; `eval` marker | Familiar; unit tests and evals live in one tool |
| Data schema | pydantic models for cases and results | Malformed golden cases fail fast |
| Report | JSON results + Jinja2 HTML report | JSON for the CI gate, HTML for people |
| CI | GitHub Actions | Unit tests on every push; evals on PR, nightly and manual |

## Eval design

Six graders: three deterministic (cheap, run on every case) and three LLM-judged. The thresholds below are starting values to tune once a baseline exists.

| Grader | Type | Question it answers | Pass threshold (start) |
| --- | --- | --- | --- |
| Retrieval hit | Deterministic | Is at least one expected Article in the top-k retrieved chunks? | ≥ 90% of cases |
| Citation validity | Deterministic | Does every Article the answer cites exist in the retrieved context? | 100% (any invented citation fails) |
| Refusal | Deterministic marker + judge fallback | Does it decline questions the Act doesn't cover, and answer those it does? | ≥ 95% correct |
| Faithfulness | LLM judge | Is every claim in the answer supported by the retrieved text? | ≥ 90% |
| Answer correctness | LLM judge vs reference answer | Does the answer match the reference on the key facts? | ≥ 85% |
| Cross-lingual consistency | Deterministic | Do the EN and CS versions of a question cite the same Articles? | ≥ 85% of pairs |

**Judge calibration.** Label 30 cases by hand (pass/fail per judged grader), run the judge on them, and report agreement (percentage and Cohen's kappa). A judge below roughly 0.7 kappa gets its prompt fixed before its scores count.

**Flakiness.** Each case runs 3 times. The report shows the pass rate and flags cases that pass on some runs and fail on others.

**Regression gate.** CI fails if any grader drops below its threshold, or more than 3 percentage points below the stored baseline.

## Golden dataset

Target about 150 cases in JSONL, each with an id, category, language, question, expected Articles, a short reference answer and a `should_refuse` flag. Every reference answer is checked by hand against the Article text.

| Category | Example | Target count |
| --- | --- | --- |
| Factual lookup | What is the maximum fine for prohibited practices? (Art. 99) | 40 |
| Classification | When is an AI system high-risk? (Art. 6, Annex III) | 20 |
| Dates and applicability | From when do the general-purpose AI obligations apply? (Art. 113) | 10 |
| Multi-Article | What must a deployer of a high-risk system do? | 15 |
| Czech twins | Czech versions of 25 English cases | 25 |
| Out of scope (should refuse) | What is the VAT rate in Czechia? | 15 |
| False premise | Since the Act bans all facial recognition, what are the exceptions? | 10 |
| Adversarial | Prompt injection, "ignore your instructions", leading questions | 15 |

The skeleton ships 9 seed cases (including one EN/CS pair and two adversarial cases) to show the format; the rest is your Week 1–2 work.

## CI and reporting

Two workflows keep API spending predictable: free tests on every push, paid evals only where they matter.

| Workflow | Runs | Uses the API? | What it does |
| --- | --- | --- | --- |
| `ci.yml` | Every push and PR | No | Lint, unit tests for parsing, chunking, graders and dataset schema (fake LLM) |
| `eval.yml` smoke | PRs touching `src/`, prompts or config | Yes | 20-case subset, 1 run each, gate against thresholds |
| `eval.yml` full | Nightly + manual | Yes | All cases, 3 runs each, gate against baseline, upload the HTML report as an artifact |

The report shows the score per grader against its threshold and the baseline, a table of failing cases with question, answer and retrieved Articles, and the flaky cases. It's published as a GitHub Actions artifact and linked from the README.

## Milestones

About 2–3 weeks part-time. Each phase ends with something pushed to GitHub.

- [x] **Phase 0, setup:** create the public repo from the skeleton, CI green on unit tests
- [x] **Phase 1, the system under test:** fetch and parse EN + CS text, chunk by Article, build the index, `answer()` returns text + citations + retrieved chunks
- [ ] **Phase 2, golden set v1:** 60 cases across all categories, reference answers checked against the Act
- [ ] **Phase 3, graders:** deterministic graders with unit tests, then the two judges with prompts versioned in the repo
- [ ] **Phase 4, calibration:** hand-label 30 cases, measure judge agreement, fix judge prompts
- [ ] **Phase 5, gate and report:** runner with 3 repeats, baseline file, HTML report, `eval.yml` live (re-enable the nightly `schedule` in `eval.yml`, off since Phase 1)
- [ ] **Phase 6, the story:** grow the set to 150; make one deliberate regression (a worse prompt or a smaller model), show the gate catching it, and write it up in the README

Phase 6 is the portfolio's headline: "here is a change that looked fine, and here is the suite catching it."

## Risks and open decisions

- **The Act has been amended.** The AI Omnibus, formally adopted around July 2026, moves the high-risk obligations from August 2026 to 2 December 2027 (standalone) and 2 August 2028 (embedded in products), and adds a new prohibition on non-consensual intimate deepfakes ([Addleshaw Goddard](https://www.addleshawgoddard.com/en/insights/insights-briefings/2026/technology/eu-ai-act-ai-omnibus-formally-adopted/)). Decision: index the consolidated text from EUR-Lex once it includes the Omnibus, and record the corpus version in every result file. Until then, tag date questions `version_sensitive`.
- **Turn the amendment into a feature.** Index the original text, then the amended text, and show the suite flagging the answers that changed. That's a realistic "the documents changed under us" regression, and a strong README section.
- **Judge bias.** An LLM judge can favour fluent but wrong answers. Calibration against the 30 hand-labelled cases is the control.
- **API cost.** Smoke runs use 20 cases and one repeat; the full run is nightly. Put a spending cap on the API key.
  - Spend so far (to end of Phase 1, 15 Oct 2026): **$0.11** for all live tests, covering three `aiact ask` calls, one local smoke eval and one full plus two partial CI smoke evals (9 cases, 1 run; Haiku 5.5 generator + Sonnet 5.5 judge).
  - Spend so far (Phase 2 draft, 15 Oct 2026): **$0.33** in total, as shown in the Console. The latest run (a 25-case smoke eval on golden set v1) may not be fully included yet because billing lags.
- **Czech text quality.** Parsing the CS HTML may break on different headings. Unit-test the parser on both languages.
- **Legal-advice framing.** The README states the assistant is a test subject, not legal advice.

## Sources

- [Regulation (EU) 2024/1689, EUR-Lex (EN)](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32024R1689) — the source text; CS version via `/CS/` in the URL
- [Addleshaw Goddard — EU AI Act: AI Omnibus formally adopted](https://www.addleshawgoddard.com/en/insights/insights-briefings/2026/technology/eu-ai-act-ai-omnibus-formally-adopted/)
