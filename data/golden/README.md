# Golden dataset

One JSON object per line. Validated by `aiact_evals.schema.GoldenCase` at load time.

| Field | Required | Meaning |
| --- | --- | --- |
| `id` | yes | Unique. Convention: `<lang>-<category>-<nnn>` |
| `category` | yes | `factual`, `classification`, `dates`, `multi_article`, `out_of_scope`, `false_premise`, `adversarial` |
| `lang` | yes | `en` or `cs` |
| `question` | yes | Exactly what a user would type |
| `expected_articles` | answerable cases | Articles/Annexes that can answer the question on their own: `"Art. 99"`, `"Annex III"`. `retrieval_hit` passes if any of them is retrieved, so don't list a supporting Article that can't answer alone (Art. 5 for "since when is X banned?" needs Art. 113). |
| `reference_answer` | answerable cases | Short expert answer the correctness judge compares against |
| `should_refuse` | refusal cases | `true` when the Act does not answer the question |
| `pair_id` | twins | Same value on an EN case and its CS twin; enables the consistency grader |
| `version_sensitive` | no | `true` when the answer depends on which version of the Act is indexed |
| `notes` | no | Why the case exists |

Rules:
- Check every `reference_answer` against the Article text yourself. A wrong reference makes the judge wrong.
- Write questions the way users ask them, not copied from the Act. Copied wording makes retrieval look better than it is.
- Add a case for every real failure you find, so it can never regress silently.
- Record the evidence. `evidence_v1.md` quotes, for every v1 reference answer, the verbatim lines of `data/processed/chunks.jsonl` it rests on. Add new cases there too.
- Don't make the reference say more than the Act. A reference that overstates the text ("Yes, staff must be trained" for Article 4) teaches the correctness judge to reward unfaithful answers.
