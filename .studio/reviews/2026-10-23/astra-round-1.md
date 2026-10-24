# Astra design consultation — 2026-10-23

This records my original design consultation, followed by one reconciliation round after reading the current repository instructions and the Kimi and Mistral reports. Recommendations are design judgments, not evidence of literary quality, model benchmarks, or runtime compatibility.

## Original consultation

The main design risk is building an efficient system for producing competent, interchangeable prose. Optimize for memorable choices, accumulated consequences, and revision that improves the book—not agent activity or checklist completion.

### Recommended initial roster

Use 14 reusable roles, with only 3–5 active on a normal task. Roles are responsibilities, not permanent concurrent agents.

| Role | Responsibility and authority boundary |
| --- | --- |
| Studio Lead | Converts the human’s intent into a bounded assignment; routes work and resolves workflow issues. Cannot redefine the creative mandate. |
| Universe Steward | Maintains accepted world rules, history, entities, and canon decisions. Records canon; does not independently invent plot. |
| Series Architect | Tracks installment differentiation, long arcs, revelations, promises, and consequences across books. |
| Book Architect | Builds and revises the book’s dramatic or argumentative structure. Outlines are hypotheses, not commands to preserve a failing plan. |
| Character Dramaturg | Tests motivation, agency, relationships, knowledge, contradictions, and change. Usually inactive for nonfiction. |
| Researcher | Collects traceable sources and useful observations; separates evidence from interpretation. |
| Drafter | Writes scenes or sections with permission to discover better local solutions within the mandate. Submits proposed continuity changes separately. |
| Developmental Editor | Evaluates structure, causality, pacing, argument, and thematic execution against the intended reading experience. |
| Independent Reader | Reads without the drafter’s explanation; reports confusion, disbelief, emotional response, and actual reader expectations. |
| Continuity Auditor | Checks chronology, physical constraints, character knowledge, rules, terminology, and cross-book consequences. |
| Fact Checker | Independently verifies substantive nonfiction claims and factual assertions requiring accuracy. Does not accept researcher summaries as proof. |
| Line Editor | Improves precision, rhythm, emphasis, and voice while preserving deliberate stylistic choices. |
| Copy Editor | Checks grammar, spelling, consistency, references, and established style. Queries intentional irregularities. |
| Release Editor | Assembles the accepted manuscript, confirms required reviews apply to its current version, and produces release artifacts. |

Character, series, and universe specialists should be conditional. A short nonfiction book should not pay the administrative cost of an epic fantasy series.

### Artifacts and ownership

Require every book to have an explicit `{universe}/{series}/{book}` identity, including standalone work. Use explicit standalone containers rather than exceptions that gradually break the structure. Shared universe and series records should have one authoritative location at their respective scope; book directories reference them rather than copying competing bibles. Keep tooling distinct from story content.

Essential artifacts:

- **Creative mandate:** audience, intended experience, distinctive promise, aesthetic principles, nonfiction scope where applicable, hard constraints, and decisions reserved for the human. Keep it short.
- **Canon registry and decision history:** accepted facts with stable IDs, source locations, scope, effective story time, and status. Separate objective facts, character beliefs, rumors, and unresolved possibilities.
- **Series ledger:** arcs, reader promises, revelations, planted elements, consequences, unresolved debts, and the earliest/latest installment where resolution remains plausible.
- **Book map:** chapters or scenes, purpose, dependencies, viewpoint, progression, and current state. Nonfiction uses claims, examples, objections, and prerequisites.
- **Working manuscript:** the authoritative prose. Avoid multiple equally plausible “final” files.
- **Research and claim ledger:** source details, supported claim, exact relevant location, confidence, qualifications, and verification status. Generated citations are not evidence.
- **Review findings:** stable finding IDs, manuscript location, evidence, severity, suggested remedy, disposition, and affected version.
- **Handoff:** current objective, accepted decisions, changed files, unresolved issues, next action, and exact source versions. This should usually fit on one page.
- **Release manifest:** manuscript version, required checks, accepted exceptions, and generated outputs.

Do not create an artifact merely because a role exists. Empty templates should not become required paperwork.

### Scene and section process

Make the scene or section the practical working unit.

A fiction packet should contain the immediate dramatic situation, relevant preceding consequences, viewpoint and character knowledge, necessary canon, local voice references, and open questions. Include only relevant context.

Evaluate scenes through questions:

- What does someone want, and what do they choose?
- What causes the next development?
- What changes in options, understanding, relationships, pressure, or expectation?
- What experience does the prose create that a summary would lose?

These are diagnostic questions, not a compulsory scene formula. Quiet, atmospheric, comic, and transitional passages need room to work differently. Character agency does not require success; it requires consequential responses rather than puppetry.

A nonfiction section instead needs its reader question, main claim, supporting evidence, strongest relevant objection, uncertainty, and contribution to the book’s larger argument. An illustrative anecdote must never silently become factual evidence.

After drafting, extract **proposed** canon changes and continuity consequences. The draft must not automatically rewrite the universe bible to make itself correct.

### Meaningful gates

1. **Direction ready:** the mandate and a small representative sample demonstrate a plausible reading experience. Do this before mass drafting.
2. **Unit ready:** the scene or section works locally; serious continuity or evidence problems are addressed or explicitly tracked.
3. **Book structurally ready:** an independent developmental read finds no unresolved structural defect that makes polishing wasteful.
4. **Language ready:** voice and prose survive line and copy editing without flattening.
5. **Release ready:** required reviews cover the assembled version; factual claims and citations are verified where applicable; outstanding exceptions are explicit.

Do not equate a numeric score with quality. A beautifully scored manuscript can still be forgettable. Gates should identify concrete blockers and accepted tradeoffs.

### Independent reviews and bounded debate

Reviewers should receive the manuscript, mandate, necessary references, and an explicit review question—not the drafter’s persuasive account of why the work succeeds. Separate sessions and independent initial judgments matter more than different model names.

For contested decisions:

1. Obtain independent initial reviews.
2. Permit one focused response or rebuttal.
3. Resolve from evidence and the mandate, or present a compact choice to the human.

Do not run debates until models converge. Consensus can amplify shared taste and error.

Use explicit per-task budgets: input context, output size, tool use, and revision attempts. A reasonable starting target is a 6–12k-token scene packet, with exceptions for actual dependencies. After two unsuccessful targeted revision cycles on the same problem, diagnose the premise or escalate the choice; do not keep paraphrasing.

Preserve the exact requested model names **Ollama Kimi K3** and **Mistral Large V4** in configuration and reports. Treat availability as something to verify. An unavailable reviewer must be reported as unavailable, never silently substituted or represented as having reviewed.

### Long-series coherence and human authority

Track three different things: what is true, what each character knows, and what the reader has been shown. Many continuity failures come from collapsing these.

Every material canon revision should identify affected books, scenes, promises, and future plans. Permit reversible experiments freely; require an explicit accepted decision before promoting a major change into shared canon. Preserve superseded decisions so abandoned ideas do not later reappear as facts.

The human’s authority should operate through the mandate, meaningful creative choices, and release decisions. Do not ask permission for routine research, drafting, reversible experiments, or ordinary corrections.

### Predictable failures

- **Bureaucracy:** require a concrete decision or downstream use for every artifact.
- **Voice averaging:** establish reference passages and explicitly preserve intentional departures from generic “good prose.”
- **Outline obedience:** allow discoveries to trigger structural revision.
- **Canon laundering:** keep proposed additions separate from accepted facts.
- **Reviewer preference laundering:** distinguish defects, risks, and taste; reviewers must explain consequences.
- **Revision churn:** retain resolved findings and reasons; reopen only with new evidence or changed text.
- **Context soup:** retrieve by scene dependencies and stable IDs, not by loading the entire repository.
- **False review coverage:** record reviewed versions and invalidate affected checks after substantive changes.
- **Invented evidence:** verify sources directly and mark unsupported claims visibly.
- **Premature polish:** solve weak choices and weak structure before optimizing sentences.

The strongest default workflow is a lead, a drafter, and an independent editor, calling specialists for specific uncertainties. The larger roster exists to supply expertise—not to make every paragraph pass through fourteen desks.

## Reconciliation round

### Scope and evidence

Read for this round: root `AGENTS.md`, `.studio/workflow.md`, `.studio/reviews/2026-10-23/kimi-k3-round-1.md`, and `.studio/reviews/2026-10-23/mistral-large-4-round-1.md`. This is a critique of those documents. I did not inspect every role contract, run the CLI, validate generated runtime adapters, or independently verify the consultation endpoints. Statements about the current implementation below refer to its documented design.

The stored report headings identify `kimi-k3:cloud` and `mistral-large-4:cloud`. Keep requested names and observed provider/model identifiers in separate fields. The headings alone do not establish that the requested “Mistral Large V4” is an officially equivalent name, or that either model ran locally.

### Concrete disagreements and resolutions

| Issue | Other reports | Reconciled recommendation |
| --- | --- | --- |
| 14 versus 16 roles | Both favor 14; Mistral counts the human among its 14. Kimi spends two roles on dialogue and knowledge boundaries. | Accept the current **16 agent roles plus the human author**. Acquisitions, art/packaging, and independent nonfiction editing justify the broader catalog. Keep dialogue under character/line editing and knowledge tracking under canon ownership. Active worker count matters more than catalog size. |
| Human approval | Kimi requires human commits and deliberate human canon acceptance. Mistral requires human PR review, outline approval, and human approval of both book and universe canon. | Prefer current `AGENTS.md`: integrate compatible details within already authorized scope; preserve provenance; escalate major retcons or unresolved author intent. No universal human commit, outline, or routine canon gate. Session authorization governs actions. |
| Model competence and cost | Kimi assigns models by assumed creative strengths and calls for hostile criticism. Mistral equates OpenCode drafting with local/cheap iteration and assumes Astra has stronger judgment. | Neither report supplies comparative task evidence, prices, or deployment measurements. Ollama is not proof of local execution; `:cloud` particularly cannot support that claim. Select with actual samples, measured cost/latency, and availability. Require specific, fair criticism rather than hostility. |
| Spoiler boundaries | Mistral says drafting context must contain only knowledge available to the viewpoint character. | The current distinction between author-visible plans and POV-permitted information is better: a writer may need a later reveal to plant an honest clue. Label disclosure restrictions explicitly; do not confuse author knowledge with narration permission. |
| Draft versioning | Mistral requires immutable `drafts/vNN/` trees and another production manuscript. | Prefer the current single manuscript source, exact snapshot hashes, and history when available. Duplicating whole draft trees creates authority ambiguity and storage noise. Preserve milestone exports when useful. |
| Stale ownership | Mistral permits timestamp-based lock expiry. | Keep current owner verification. A slow worker is not a dead worker, and a timestamp does not authorize concurrent writes. |
| Automation | Both discourage early automation, while Mistral also requests structural linting. | The proposed small standard-library CLI is proportionate: scaffold, validate structure, assemble in explicit order, prepare bounded packets, and generate adapters. It must report mechanical checks without certifying prose quality or truth. No workflow engine is needed. |

### Important remaining gaps to verify or tighten

1. **Assign direct factual verification explicitly.** The 16-role roster removes my separate Fact Checker. That is acceptable only if an independent `nonfiction_editor` assignment includes opening original sources and verifying consequential claims, quotations, and locators—not merely evaluating a researcher's evidence summary. For fiction with material factual claims, the same independent check can be assigned to a fresh researcher session. Record actual claim coverage and omissions. A new seventeenth role is unnecessary.
2. **Make review packets resistant to contamination.** The documented default packet includes handoff, outline, and style. Handoffs and outlines may contain the drafter's rationale or prior verdicts. Independent reader/developmental assignments need an explicit initial input list that excludes these unless necessary. The workflow already describes this distinction; verify that the CLI's convenient default does not undermine it.
3. **Finish the budget and retry contract.** The example task budget limits rounds and output words but does not demonstrate input-context or tool-call limits. Add explicit per-task limits where needed and a response to repeated failure: stop local rewriting, identify the disputed premise, and try a small alternative or seek a consequential creative decision. Budget exhaustion must produce a truthful partial handoff, not a fabricated pass.
4. **Keep state changes atomic in meaning.** Canon acceptance touches proposed status, accepted facts, revision counters, and decision records. Ensure an interrupted application is detectable and recoverable; do not let an “accepted” flag survive without its fact and decision. This can be a documented transaction checklist or a small checked helper, not a database.
5. **Specify packaging ownership and truthful claims.** Acquisitions owns audience/positioning; art owns visual briefs; production owns final metadata and assembly. Identify who writes and reviews blurbs, jacket copy, contents, notes, and accessibility text. Marketing copy must not invent endorsements, credentials, awards, or claims about the book. The art role should produce briefs within its authorized scope; it need not generate images.
6. **Preserve whole-book reading as a real task.** A series of scene approvals is insufficient to establish cumulative pacing, repetition, argument progression, or an earned ending. The development gate correctly calls for a whole-book read; when context limits require staged reading, preserve ordered reading notes and disclose coverage rather than claiming a simultaneous full-manuscript evaluation.

### Final recommendation

Proceed with the documented 16-role design and the small CLI. Its strongest choices are the direct `{universe}/{series}/{book}` hierarchy, proposed-versus-accepted canon, chronological knowledge tracking, cold independent reviews, authorized routine integration, bounded disagreement, and one authoritative set of portable role contracts.

The next meaningful validation is a small fiction scene and a sourced nonfiction section through the complete loop, including a deliberate continuity error and an unsupported claim. Verify that reviewers catch them, findings remain tied to the reviewed snapshot, and a targeted revision does not erase the voice. Do not expand the role roster or workflow machinery before that exercise reveals a concrete need.
