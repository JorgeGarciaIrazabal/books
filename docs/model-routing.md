# Provisional model routing

The author approved using the available recommendations despite incomplete tests.
These settings were adopted on 2026-10-25. `.studio/roster.json` is the source for
actual per-runtime routes, effort, task overrides, and preferred inactive routes.

| Phase / role | Codex model | Effort | Basis |
| --- | --- | --- | --- |
| Direction, universe, series | GPT-6.1 Sol | High | Provisional extension of planning results; these whole roles were not isolated in the benchmark |
| Premise development | GPT-6.1 Sol | High | Split concept result; acquisitions task override |
| Plot and scenes | GPT-6.1 Sol | High | Stronger initial planning comparison |
| Character and dialogue | GPT-6.1 Sol | High | Initial character/dialogue comparison |
| Drafting | GPT-6.1 Sol | High | Provisional choice from a split drafting result |
| Developmental editing | GPT-6.1 Sol | Medium | Provisional choice from a split review result |
| Line editing | GPT-6.1 Sol | High | Initial line-edit comparison |
| Copy and continuity | GPT-6.1 Sol | High | Initial combined copy/canon comparison; separate native roles |
| Blurbs and catalog copy | GPT-6.1 Sol | Medium | Initial blurb comparison; acquisitions default |
| Independent reader | GPT-6 Sol | High | Different-model perspective; no isolated reader-role benchmark |
| Research | GPT-6 Astra | Medium | Existing setting retained; specialty untested |
| Nonfiction editing | GPT-6 Astra | High | Existing setting retained; specialty untested |
| Production and art | GPT-6 Astra | Medium | Existing settings retained; specialties untested |

The Codex main-session and generic-child defaults are GPT-6.1 Sol high. Named
agent settings take precedence. The acquisitions role defaults to medium; the
director must explicitly invoke high for premise development. Merely recording
a task override does not change a running agent's effort. Use a fresh session for
new project defaults and disclose unavailable models.

A fresh developmental editor using the same model as the drafter has an
independence limit. Supply the brief and actual text without prior verdicts or
the writer's defense, then obtain the separately assigned GPT-6 Sol reader response
for major drafts. A model vote does not establish truth or canon.

## Active OpenCode fallbacks

The native Sol OpenRouter probe returned HTTP 403 because the connected API key
had reached its spending cap. No account limit or credentials were changed.
`opencode_preferred_model` records the intended Sol route; it does not activate it.

| Active model / effort | OpenCode roles |
| --- | --- |
| Kimi K3 high | Director, universe, series, story, research, development, canon, reader, nonfiction, production |
| Mistral Large 4 high | Acquisitions, character, drafting, line, copy, art |

Kimi gives the active Mistral drafter a different-model reader. These fallback
choices preserve usable provider routes and are not claims that corrected
medium/high comparisons established winners. All native files use explicit
`#high` variants, and model defaults also set `reasoning_effort: high`.

The compatible endpoint is `/v1/chat/completions`; its control is
`reasoning_effort`, not the native `think` field. Kimi exposes low/high/max and
Mistral none/high on the tested route. The author approved low/high for Kimi and
supported equivalents for Mistral; none is labeled none, never medium.

## Instruction changes adopted

The shared director contract now requires accurate route descriptions, relevant
source packets, disclosure of same-model review limits, and separation of prose
from state deltas and process notes. The story architect checks time, deadlines,
resources, restarts, knowledge, and the consequences of later beats. The drafter
uses style samples for craft rather than copying their sentences and checks final
actions, custody, and knowledge against the scene contract. The canon keeper
verifies quotations and locators, distinguishes definite errors from queries,
and proposes repairs that preserve downstream constraints.

These are short editorial safeguards motivated by observed failures. The longer
experimental instruction packages were not adopted wholesale and did not pass a
complete paired comparison. Scene word budgets and note allowances remain separate;
a runtime step-limit summary must not be treated as manuscript prose.

## Evidence and limits

The [original phase report](../bellwether-reach/the-flood-ledgers/the-ninth-lock/benchmark/report.md)
preserves the initial ranking with a prominent effort-control correction.
The original Kimi/Mistral effort comparisons were withdrawn because their control
field was ineffective. Sol conditions were unaffected by that defect. Samples
were short, based on one novel fixture, and judged by models; they do not establish
whole-book reliability or a universal best model.

The [instruction experiment](../.studio/experiments/instruction-ablation-v1/handoff.md)
stopped with 15 of 16 complete primary candidate runs, each covering three phases
on two fixtures, and one valid peer review. One other peer response was invalid
JSON; no final aggregate verdict was produced. Corrected cloud samples are kept
separate from superseded preflight samples. Partial findings include timing
mistakes, citation-location faults, and overcorrection of valid controls. Longer
instructions did not show consistent enough gains to claim superiority.

The author authorized this provisional adoption instead of waiting for completion.
The [adoption handoff](../.studio/reviews/provisional-adoption/handoff.md) records
changed files, actual verification, operational limits, and the next action.
