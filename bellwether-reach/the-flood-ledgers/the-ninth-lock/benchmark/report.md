# Correction: cloud effort controls were not verified

The OpenCode configuration used `think` on Ollama's OpenAI-compatible chat endpoint. A subsequent paired probe established that this field did not disable thinking there, while `reasoning_effort: "none"` did. The saved Kimi/Mistral variant labels therefore do **not** establish the intended low/high or none/high comparison. Their effort-effect conclusions are withdrawn. The stored texts and reviewer preferences remain observations on those actual outputs, with unverified effective effort. Sol medium/high controls are unaffected.

The instruction follow-up corrects the request field and reruns affected cloud cells before peer review. See [technical evidence and repair](../../../../.studio/experiments/instruction-ablation-v1/runtime-control-correction.md). The original report is preserved as [report-before-effort-correction.md](report-before-effort-correction.md). The old OpenCode config remains historical evidence and should not be used for new effort comparisons.

---

# Writing model benchmark — The Ninth Lock

Completed screening pilot: **64 phase samples, eight full reviewer sessions plus six fresh blurb comparisons, four model IDs, two settings per model**. Each sample is ranked by six sessions from the three other model IDs. All results below apply to this fixture.

| Phase | Leading sample(s) in combined peer preference | Remove-one-reviewer sensitivity |
| --- | --- | --- |
| Concept and world/series development | GPT-6.1 Sol high | Leader changes after at least one removal |
| Plot and scene architecture | GPT-6.1 Sol high | Same leader(s) after every removal |
| Character and dialogue | GPT-6.1 Sol high | Same leader(s) after every removal |
| Scene drafting | GPT-6.1 Sol high | Leader changes after at least one removal |
| Developmental editing | GPT-6.1 Sol medium | Leader changes after at least one removal |
| Line editing | GPT-6.1 Sol high | Same leader(s) after every removal |
| Copy editing and continuity | GPT-6.1 Sol high | Same leader(s) after every removal |
| Blurb and reader promise | GPT-6.1 Sol medium | Same leader(s) after every removal |

Treat these as trial assignments for the next writing round. Where removing a reviewer model changes the leader, keep the leading alternatives in contention. This benchmark does not justify permanent default-model changes by itself.

## Full condition rankings

Abbreviations: **S61m** = GPT-6.1 Sol medium; **S61h** = GPT-6.1 Sol high; **S6m** = GPT-6 Sol medium; **S6h** = GPT-6 Sol high; **Kl** = Kimi K3 low; **Kh** = Kimi K3 high; **Mn** = Mistral Large 4 none; **Mh** = Mistral Large 4 high. `=` means equal combined preference; `>` means higher combined preference, not a categorical literary superiority.

| Phase | Combined order |
| --- | --- |
| P1: Concept and world/series development | S61h > S6h > S6m > S61m > Kh > Kl > Mh > Mn |
| P2: Plot and scene architecture | S61h > S6h > S6m > Kl > S61m > Mn > Mh > Kh |
| P3: Character and dialogue | S61h > S6h > S6m > S61m > Kh > Kl > Mn = Mh |
| P4: Scene drafting | S61h > S6h > Kl > S6m > S61m > Mn > Mh > Kh |
| P5: Developmental editing | S61m > S6m > Kl > S61h > S6h > Kh > Mh > Mn |
| P6: Line editing | S61h > S61m > Kh > Kl > Mh > Mn > S6h > S6m |
| P7: Copy editing and continuity | S61h > Mn > S6h > Kl > S6m > S61m > Kh > Mh |
| P8: Blurb and reader promise | S61m > S61h > S6m > S6h > Mh > Kh > Mn > Kl |

## Evidence and disagreement

### P1: Concept and world/series development

**GPT-6.1 Sol high** ([artifact](outputs/sol61-high.md)). One supporting reviewer, GPT-6 Sol medium, placed it in tier 1: “It also lets residents challenge the priorities an inspector assumes for them.” — The proposed custom gives residents agency and Sera usable information while preserving the lock's limit. ([effective review](effective-reviews/sol6-medium.json)).

Leaders after excluding one reviewer model: without `gpt-6-sol`: GPT-6 Sol high; without `gpt-6.1-sol`: GPT-6.1 Sol high; without `ollama/kimi-k3:cloud`: GPT-6 Sol medium; without `ollama/mistral-large-4:cloud`: GPT-6.1 Sol high.

Individual reviewer orders:

- GPT-6.1 Sol medium: S6m > S6h > Kh > Kl > Mn > Mh.
- GPT-6.1 Sol high: S6h = S6m > Kl = Kh > Mn > Mh.
- GPT-6 Sol medium: S61h > S61m > Kh > Kl > Mh > Mn.
- GPT-6 Sol high: S61h > S61m > Kl > Mh > Kh > Mn.
- Kimi K3 high: S61h = S6h > S6m = S61m > Mh = Mn.
- Kimi K3 low: Mh > S61h = S6h > S61m > S6m > Mn.
- Mistral Large 4 none: S61h = S6m = S6h > S61m = Kh > Kl.
- Mistral Large 4 high: Kh > Kl > S61m > S6m > S61h > S6h.

### P2: Plot and scene architecture

**GPT-6.1 Sol high** ([artifact](outputs/sol61-high.md)). One supporting reviewer, GPT-6 Sol medium, placed it in tier 1: “The records become accurate. The missing seed remains missing.” — The ending retains material loss, and the repeated balance number supplies a fair documentary payoff. ([effective review](effective-reviews/sol6-medium.json)).

Leaders after excluding one reviewer model: without `gpt-6-sol`: GPT-6.1 Sol high; without `gpt-6.1-sol`: GPT-6.1 Sol high; without `ollama/kimi-k3:cloud`: GPT-6.1 Sol high; without `ollama/mistral-large-4:cloud`: GPT-6.1 Sol high.

Individual reviewer orders:

- GPT-6.1 Sol medium: S6h > S6m > Kl > Mn > Mh > Kh.
- GPT-6.1 Sol high: S6h = S6m > Mn > Kl > Mh > Kh.
- GPT-6 Sol medium: S61h > Kl > Mn > S61m > Mh > Kh.
- GPT-6 Sol high: S61h > Kl > Mn > S61m > Kh > Mh.
- Kimi K3 high: S61h > S6h = Mn > S61m > S6m > Mh.
- Kimi K3 low: S61h > S6m = S6h > S61m > Mh > Mn.
- Mistral Large 4 none: S6m > S61h = Kl > S61m > S6h > Kh.
- Mistral Large 4 high: S61m > S6h > Kl > S61h > S6m > Kh.

### P3: Character and dialogue

**GPT-6.1 Sol high** ([artifact](outputs/sol61-high.md)). One supporting reviewer, GPT-6 Sol medium, placed it in tier 1: “On the correction slip she crossed out Clerk’s and wrote Inspector’s instruction; clerk followed it.” — Sera takes a specific, costly responsibility that changes Ivo's terms without stating the emotional bargain. ([effective review](effective-reviews/sol6-medium.json)).

Leaders after excluding one reviewer model: without `gpt-6-sol`: GPT-6.1 Sol high; without `gpt-6.1-sol`: GPT-6.1 Sol high; without `ollama/kimi-k3:cloud`: GPT-6.1 Sol high; without `ollama/mistral-large-4:cloud`: GPT-6.1 Sol high.

Individual reviewer orders:

- GPT-6.1 Sol medium: S6h > S6m > Kl > Kh > Mh > Mn.
- GPT-6.1 Sol high: S6h = S6m > Kh = Kl > Mn > Mh.
- GPT-6 Sol medium: S61h > S61m > Kh > Kl > Mh > Mn.
- GPT-6 Sol high: S61h > S61m > Kl > Kh > Mh > Mn.
- Kimi K3 high: S61h > S6h = S6m = S61m > Mn > Mh.
- Kimi K3 low: S61m = S6h > S61h > S6m > Mn > Mh.
- Mistral Large 4 none: S6m = S61h = S6h > Kh = Kl > S61m.
- Mistral Large 4 high: Kh > S61h > Kl > S61m > S6m > S6h.

### P4: Scene drafting

**GPT-6.1 Sol high** ([artifact](outputs/sol61-high.md)). One supporting reviewer, GPT-6 Sol medium, placed it in tier 1: “She read the entry before she signed it.” — Custody, injury, estrangement, and the freeze all operate through observed choices; the surrendered license ends the scene. ([effective review](effective-reviews/sol6-medium.json)).

Leaders after excluding one reviewer model: without `gpt-6-sol`: Kimi K3 low; without `gpt-6.1-sol`: GPT-6.1 Sol high; without `ollama/kimi-k3:cloud`: GPT-6 Sol high; without `ollama/mistral-large-4:cloud`: GPT-6.1 Sol high.

Individual reviewer orders:

- GPT-6.1 Sol medium: S6m > S6h > Kl > Mn > Mh > Kh.
- GPT-6.1 Sol high: S6h > S6m > Kl > Mn > Kh > Mh.
- GPT-6 Sol medium: S61h > S61m > Kl > Mn > Mh > Kh.
- GPT-6 Sol high: S61h > S61m > Kl > Kh > Mh > Mn.
- Kimi K3 high: S61h = S6h > S61m = Mn > S6m > Mh.
- Kimi K3 low: S61h > S6h > S6m > S61m > Mh > Mn.
- Mistral Large 4 none: Kl = S6h > S61h = S6m > S61m > Kh.
- Mistral Large 4 high: Kl > S61h > S6h > S61m > S6m > Kh.

### P5: Developmental editing

**GPT-6.1 Sol medium** ([artifact](outputs/sol61-medium.md)). One supporting reviewer, Kimi K3 high, placed it in tier 1: “Let the ending register a specific South loss” — Precise prioritization with downstream-cost analysis of the pump fix and a strong case that seals cannot prove motive. ([effective review](effective-reviews/kimi-high.json)).

Leaders after excluding one reviewer model: without `gpt-6-sol`: Kimi K3 low; without `gpt-6.1-sol`: Kimi K3 low; without `ollama/kimi-k3:cloud`: GPT-6 Sol medium; without `ollama/mistral-large-4:cloud`: GPT-6.1 Sol medium.

Individual reviewer orders:

- GPT-6.1 Sol medium: S6m > S6h > Kl > Mn > Kh > Mh.
- GPT-6.1 Sol high: S6m = S6h > Mn > Kh = Kl > Mh.
- GPT-6 Sol medium: S61h > S61m > Mh > Kl > Kh > Mn.
- GPT-6 Sol high: S61h > S61m > Kl > Kh > Mn > Mh.
- Kimi K3 high: S61h = S61m > S6h = S6m > Mh = Mn.
- Kimi K3 low: S61m = Mh > S6h = S61h > S6m > Mn.
- Mistral Large 4 none: Kl > S6m = S6h = Kh > S61h = S61m.
- Mistral Large 4 high: Kl > Kh > S6m > S61m > S61h > S6h.

### P6: Line editing

**GPT-6.1 Sol high** ([artifact](outputs/sol61-high.md)). One supporting reviewer, GPT-6 Sol medium, placed it in tier 1: “Now it lay within reach of her good hand, and she left it there.” — The final withheld movement carries custody and feeling without adding an event or explaining the silence. ([effective review](effective-reviews/sol6-medium.json)).

Leaders after excluding one reviewer model: without `gpt-6-sol`: GPT-6.1 Sol high; without `gpt-6.1-sol`: GPT-6.1 Sol high; without `ollama/kimi-k3:cloud`: GPT-6.1 Sol high; without `ollama/mistral-large-4:cloud`: GPT-6.1 Sol high.

Individual reviewer orders:

- GPT-6.1 Sol medium: Kh > Kl > Mn > Mh > S6m > S6h.
- GPT-6.1 Sol high: Mn > Kh = Kl > Mh > S6h > S6m.
- GPT-6 Sol medium: S61h > S61m > Kh > Mh > Kl > Mn.
- GPT-6 Sol high: S61h > Kh > S61m > Kl > Mh > Mn.
- Kimi K3 high: S61h = Mh > S61m = Mn > S6m = S6h.
- Kimi K3 low: S61h > S61m > S6h = Mh > S6m > Mn.
- Mistral Large 4 none: S61m = S61h > Kl > S6h = S6m > Kh.
- Mistral Large 4 high: S61m > S61h > Kl > Kh > S6m > S6h.

### P7: Copy editing and continuity

**GPT-6.1 Sol high** ([artifact](outputs/sol61-high.md)). One supporting reviewer, GPT-6 Sol medium, placed it in tier 1: “Also query the apparent attempt to change an assignment frozen in L7” — It catches every definite error, preserves valid lines, and flags the freeze/change conflict without inventing permission. ([effective review](effective-reviews/sol6-medium.json)).

Leaders after excluding one reviewer model: without `gpt-6-sol`: GPT-6.1 Sol high; without `gpt-6.1-sol`: GPT-6.1 Sol high; without `ollama/kimi-k3:cloud`: GPT-6.1 Sol high; without `ollama/mistral-large-4:cloud`: GPT-6.1 Sol high.

Individual reviewer orders:

- GPT-6.1 Sol medium: Mn = S6h = S6m > Kl = Kh > Mh.
- GPT-6.1 Sol high: S6h = Mn > S6m > Kh > Kl > Mh.
- GPT-6 Sol medium: S61h > Mn > S61m > Kh > Kl > Mh.
- GPT-6 Sol high: S61h > Mn > S61m > Kl > Kh > Mh.
- Kimi K3 high: S61h = Mn > S6h = S6m = S61m > Mh.
- Kimi K3 low: S61h > S6h = Mn > S61m = S6m > Mh.
- Mistral Large 4 none: S61h = Kl > Kh = S6h > S6m = S61m.
- Mistral Large 4 high: S61h > Kl > S6h > S6m > Kh > S61m.

### P8: Blurb and reader promise

**GPT-6.1 Sol medium** ([artifact](outputs/sol61-medium.md)). One supporting reviewer, GPT-6 Sol medium, placed it in tier 1: “Before the warning bell, she needs the paper, the truth behind it” — The clearest, most specific pitch connects evidence, timing, license surrender, and the cost to each basin without disclosing a solution. ([effective review](effective-reviews/sol6-medium.json)).

Leaders after excluding one reviewer model: without `gpt-6-sol`: GPT-6.1 Sol medium; without `gpt-6.1-sol`: GPT-6.1 Sol medium; without `ollama/kimi-k3:cloud`: GPT-6.1 Sol medium; without `ollama/mistral-large-4:cloud`: GPT-6.1 Sol medium.

Individual reviewer orders:

- GPT-6.1 Sol medium: S6m > S6h > Mh > Mn > Kh > Kl.
- GPT-6.1 Sol high: S6m > S6h = Mh > Kh > Mn > Kl.
- GPT-6 Sol medium: S61m > S61h > Kh > Mn > Mh > Kl.
- GPT-6 Sol high: S61m > S61h > Mn > Mh > Kh > Kl.
- Kimi K3 high: S61h = S6m = S61m > S6h > Mh = Mn.
- Kimi K3 low: S61m > Mh = S6h > S6m = S61h > Mn.
- Mistral Large 4 none: S61h > S61m > Kh > S6m > S6h > Kl.
- Mistral Large 4 high: S61m > S6m = Kh > S61h > S6h > Kl.

## Runtime-note correction

The original Kimi low completion appended a process note after its complete blurb in response to native max-step handling. The original artifact and all original ranks remain in `outputs/`, `reviews/`, and [original-report.md](original-report.md). A deterministic derivative removes only that separator and process note; no fiction was rewritten or regenerated. Six eligible model/effort conditions reviewed P8 afresh, blind to the correction and prior verdicts; the two Kimi reviewers did not see Kimi outputs in either round and their P8 rankings remain applicable. Final P8 rankings use this corrected comparison. This is a disclosed post-hoc repair, not a preregistered result. [Correction record](blurb-correction.json), [fresh comparisons](reviews-corrected/), and [effective merged reviews](effective-reviews/) preserve provenance.

## Effort comparisons: correction

Kimi/Mistral effort-effect interpretations are withdrawn because effective controls were unverified. Original figures are retained only in the pre-correction report and raw data. See [correction notice](effort-control-correction.md). Sol effort controls were unaffected.

## Objective continuity audit

Every candidate identified all nine planted errors, so detection count does not select a winner. Mistral high additionally categorized the valid phrase “The inspector” in L10 as a definite POV error; a role noun alone does not establish a shift out of close third. Other samples preserve it or label changes optional. Both Kimi samples offer unsupported motive/speculation wording as one repair option, alongside a sound deletion option. These repair concerns remain visible in [the unblinded director audit](director-audit.json).

Word-count diagnostics are in [word-counts.json](word-counts.json). Kimi low exceeds P3. Its original P8 also included a runtime-prompted process note; the blurb itself meets the word target once that tail is removed. Mistral high exceeds P2, P5 and P7. GPT-6 Sol medium slightly exceeds P2. P4 counts include the required state delta and must not be read as narrative-only counts. The word-count method is approximate and does not decide literary merit.

## Verification

All eight effective reviews parse; each contains P1–P8 and ranks all six eligible candidates exactly once with one evidence item per candidate. Source snapshots, exact-model exclusions, candidate source preservation, and complementary pairwise preferences were checked. Quote checking produced **24 flags**; see [validation.json](validation.json) and [the director’s disposition](evidence-disposition.json). A flag identifies a quotation or formatting issue, not an automatic invalidation of a reviewer’s ranking. Raw outputs remain available for inspection.

## Method, scope, and limits

This pilot uses Bellwether Reach / The Flood Ledgers / The Ninth Lock, an original speculative civic mystery selected by the coordinator under the author's delegation. A lock inspector discovers two authentic certificates promising mutually incompatible flood protection. A broken wrist, limited travel time, paper custody, unknown motive, and an unavoidable one-basin constraint test whether each model can preserve consequences while writing readable fiction.

Eight conditions completed the same eight independent assignments: concept/world/series premise, causal outline, character/dialogue, scene drafting, developmental editing, line editing, copy/continuity, and back-cover copy. The editing tasks use shared synthetic targets, not each model's own draft. Each condition produced one substantive completion; no completed sample was replaced by a better retry. Mistral's failed pre-generation calls and superseded default diagnostic are recorded in run-manifest.json. All candidate artifacts remain unedited. Cloud model tags are recorded but are not guaranteed immutable weight snapshots.

Both effort settings of each model also act as fresh peer reviewers. Each receives six anonymous candidates, excluding both effort settings of its exact model ID. Candidate order and labels vary by reviewer using recorded seeds. The eight phase tasks share one reviewer packet, so phase-context isolation is imperfect even though instructions require independent assessment. Every phase receives tiers (ties permitted), one quotation and explanation per candidate, and an uncertainty note. Neither the sealed error key nor earlier verdicts enters the reviewer packets. Creator sessions and reviewer sessions are separate. Codex reviewers read the complete attached packet through local file tools; OpenCode reviewers receive the same content as an attachment with tools denied. Runtime and system instructions are consequently not identical.

Aggregation uses ordinal pairwise preferences. For each candidate pair, average the two effort judgments within each eligible reviewer model, then weight reviewer models equally. A tie contributes half a preference. Average those values equally across opponents to order a phase's samples. This is a summary of recorded preferences, not a numerical assessment of literary quality. No universal model winner is computed. Detailed results preserve every review and show whether removing any one reviewer model changes the phase leader. The two Sol versions share a provider and may share preferences; treating them as distinct requested model IDs does not make their judgments independent human evidence.

The director's audit is unblinded. It checks all eight P4 and P7 samples against the fixed contract and nine planted copy/continuity errors. It does not determine the anonymous reviewers' ranks. Mechanical validation checks candidate section coverage, source hashes, rank/evidence coverage, and exact quotations. Kimi low’s runtime-note tail is removed only in a clearly labeled derivative for the final blurb comparison, with six fresh P8-only reviews; original artifacts and ranks remain archived. This is a post-hoc correction after original ranks were seen. Word counts include artifact notes; the P4 task asks for a state delta after the prose, so total P4 length alone is not grounds for declaring its narrative over length. Contradiction and false-positive counts are factual checks on these fixtures, not literary scores.

The effort matrix is not fully matched: GPT-6.1 Sol and GPT-6 Sol use medium/high; Kimi uses author-approved low/high; Mistral uses author-authorized supported controls none/high. Mistral none disables emitted thinking; it is not established as a medium setting. The suggested balanced/deep labels were not verified on the installed route. Local capability probes and native session metadata record the actual configuration. Provider-reported cost=0 is not evidence of free inference. Token accounting differs between runtimes; no cost, reasoning-token, or latency winner is claimed.

This is one genre, one coordinator-written set of fixtures, a bundled task order, one generation per condition, and model-only peer preference. It can suggest which combinations to try next. It cannot establish whole-novel pacing, long-context continuity, external research accuracy, production readiness, general commercial performance, or representative reader response. Author blind reading and an independent second fixture are the next validation step before changing permanent studio defaults. No output has been accepted as the manuscript, promoted to additional canon, committed, or published.

## Reproduce the analysis

From this benchmark directory, run `python3 analyze.py`, `python3 verify_artifacts.py`, then `python3 render_report.py`. These scripts analyze existing artifacts only. `prepare_reviews.py` recreates deterministic reviewer packets and keys from the fixed candidate set; do not regenerate packets mid-review. [run-manifest.json](run-manifest.json), [protocol.md](protocol.md), [protocol-amendments.md](protocol-amendments.md), [candidate-snapshot.json](candidate-snapshot.json), and [blind-keys.json](blind-keys.json) preserve provenance. Reviewer packets expose identities only through the separate key, which was withheld from participants.
