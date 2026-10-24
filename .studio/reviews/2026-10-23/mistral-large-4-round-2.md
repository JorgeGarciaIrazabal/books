# mistral-large-4:cloud — consultation

I'll review the supplied documents and give my focused final critique.

---

## Final design critique — round 2

### (1) What I change in my original recommendation

Reading Kimi and Astra, I withdraw several of my stronger positions:

- **I no longer defend a 14-role roster.** The current 16-role catalog plus human is defensible. Kimi's "dialogue polisher" and "knowledge boundary setter" collapse into existing character/canon work; Astra's reconciliation is correct that active worker count matters more than catalog size. I would not add a 17th role, but I would not prune either.

- **I abandon "human always commits / approves every canon acceptance."** Kimi's gatekeeping model creates exactly the bureaucratic churn the brief warns against. The current "authorized scope + provenance + escalate major retcons" is better for a working studio. My original position would have made routine compatible additions require human interruption.

- **I retract my cross-model "best model for each job" assignment.** Kimi's Astra-as-architect / Mistral-as-drafter / Kimi-as-critic split assumes comparative competence neither report evidences. Astra is right: these are unbenchmarked starting choices. The CLI should record *which* model ran, not presume a hierarchy.

- **I accept the single working manuscript over Kimi's immutable `drafts/vNN/` trees.** Snapshot hashes solve the authority problem without storage duplication.

What I keep: independent cold review (both agree, and it's correct), bounded debate (both agree on ~2 turns), proposed-vs-accepted canon separation, and the anti-overengineering starter path.

### (2) Remaining high-impact defects/omissions

**A. Review-packet contamination is still a live risk, not a verified fix.** Astra flagged that the default packet includes handoff and outline; workflow.md now excludes them for `--mode review`. But the CLI's *default* (non-review) packet still bundles handoff + outline, and a rushed coordinator may reuse a drafting packet for a "review." The defect is that the *convenient* path is the contaminated one. Make `--mode review` the safe default for any Independent Reader / Developmental Editor / Nonfiction Editor assignment, or require an explicit `--acknowledge-rationale` flag when those roles receive handoff/outline. This is the single highest-leverage remaining rule.

**B. Independent factual verification has no named owner.** The 16-role roster dropped Astra's Fact Checker. Astra's reconciliation accepts this *only if* `nonfiction_editor` is contractually required to open original sources for consequential claims. I see no evidence in AGENTS.md or workflow.md that the `nonfiction_editor` contract contains this requirement. It currently reads as thesis/logic/pedagogy/evidence-sufficiency — argument evaluation, not source inspection. For a nonfiction book, "does the evidence support the claim" *demands* reading the source. For fiction with embedded factual claims (dates, places, procedures), no role is assigned this. **Fix:** add an explicit sentence to the `nonfiction_editor` and `researcher` contracts — "verify consequential claims against original sources; do not accept another role's summary as proof" — and allow `researcher` to be assigned a fresh independent verification pass on fiction. Record claim coverage in `research/claims.json`.

**C. Character/reader/author knowledge has three states but only two are mechanically protected.** `knowledge.json` tracks "character AND reader disclosure boundaries." But the author-knows/plans-to-reveal state lives in outlines and series promises — exactly the files excluded from review packets. This is correct for *review* contamination but creates a different failure: the **drafter** may receive a scene contract where "forbidden early revelations" is under-specified because the author's future plan wasn't translated into the contract. The scene contract template in workflow.md lists "permissible disclosures, forbidden early revelations" — good — but there's no check that these were *derived* from the series promises. **Fix:** require the canon_keeper or director to populate `forbidden_early_revelations` in `scenes.json` (or the scene contract) by referencing specific series-promise IDs, not free text. A drafter should not have to infer spoiler boundaries.

**D. Voice preservation across revision is asserted, not enforced.** Astra's "voice averaging" and Kimi's "AI-isms" warnings are both about the line editor flattening distinctive prose. AGENTS.md says "Do not flatten unusual voice" and "preserve user edits" — principles, not mechanisms. The acceptance check "targeted revision does not erase the voice" (Astra's final recommendation) has no operational definition. **Fix:** require every line-edit assignment to include 1–2 reference passages from the *current draft* (not just `style.md` samples) and to return a diff-style change list where each substantive change is justified against "what experience does this preserve?" The line editor's deliverable should include "deliberate departures preserved" as an explicit line.

**E. Packaging ownership is named but not specified.** Astra flagged this; the brief repeats it. `production_editor` "owns assembly, metadata, release QA." `acquisitions_editor` "owns premise, audience, positioning." `art_director` "owns cover/series visual identity, accessibility." But who writes the *back-cover copy*? Who approves the *catalog description*? These are the highest-risk marketing artifacts (invented endorsements, credential inflation) and they sit in the gap between acquisitions (positioning) and production (metadata). **Fix:** one sentence in AGENTS.md or workflow.md: acquisitions drafts audience-facing copy (blurb, positioning, comp titles); production reviews it for truthful claims before release; art provides visual briefs only. Explicitly: no role may invent endorsements, awards, or credentials.

**F. Whole-book coverage disclosure is a rule, not a field.** workflow.md says "disclose which parts were actually covered" for staged reading. But `reviews/gates.json` has no schema field for coverage. A developmental editor who read chapters 1–8 and skimmed 9–15 can record "pass" with a note; the note is prose, not data. **Fix:** require every developmental/nonfiction review report to include a machine-readable coverage object: `{chapters_read_in_full: [...], chapters_skimmed: [...], sections_not_assessed: [...], word_count_assessed: N}`. A gate recorded without this object is incomplete.

### (3) Three acceptance checks

1. **Contamination check.** Run one independent developmental review using only `packet --mode review`. Confirm the packet contains zero bytes from `handoff.md` or `outline.md`, and that the reviewer's report does not reference drafter rationale. Then run the same review with the *default* packet and confirm the CLI either refuses or prints a loud warning when an independent-reviewer role is assigned. *Pass:* the safe path is the default; the unsafe path is visibly marked.

2. **Source-inspection check.** Take one nonfiction section containing three consequential factual claims (a statistic, a quotation, a historical date). Assign `nonfiction_editor` to audit it. Confirm the report cites original source locators (page, URL, timestamp) for each claim, marks any unsupported claim as unsupported, and does not rely solely on `research/claims.json` summaries. *Pass:* every consequential claim has an independent source locator or is flagged.

3. **Knowledge-boundary check.** Plant one deliberate spoiler violation in a draft scene: a character references information they cannot yet know, where that information is a planned series promise. Run the drafter → canon_keeper loop. *Pass:* the canon_keeper's continuity report catches the violation, ties it to the specific `knowledge.json` / series-promise ID, and the targeted revision fixes the disclosure without deleting the planted clue's *function* (the clue survives via a POV-permitted channel). separat

---

**Uncertainty stated:** I have not inspected the 16 role contracts, the CLI source, or the generated adapters. My claims about what `nonfiction_editor` is contractually required to do are inferred from AGENTS.md's one-line responsibility descriptions, not from the contract files. If those contracts already contain source-inspection and coverage-disclosure requirements, defects B and F reduce to "verify and test" rather than "add."
