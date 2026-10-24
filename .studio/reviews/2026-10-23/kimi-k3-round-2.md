# kimi-k3:cloud — consultation

After reviewing the Astra reconciliation and the current AGENTS.md/ workflow.md operating rules, my final assessment is:

**1. Changes from my original recommendation**

I retract my advocacy for a 14-role roster as a fixed ceiling. The current 16-role design is superior. Explicitly adding `acquisitions_editor`, `art_director`, and `nonfiction_editor` fills genuine gaps in a professional studio pipeline. My prior suggestion for immutable `drafts/vNN/` directories is also inferior to the current design: a single working manuscript with hashed snapshot builds and strict review versioning is cleaner, provided `reviews/gates.json` explicitly records which text the review covers. 

I maintain my insistence on separating author knowledge, reader knowledge, and character knowledge, but I accept the current `knowledge.json` implementation. I also withdraw my rigid "only POV-permitted info in drafting context" rule. Astra’s distinction—labeling author-visible plans versus POV disclosures—is better for planting authentic clues. Finally, I abandon cross-model human PR review as a default merge gate; the coordinator’s authorized-scope integration is far less bureaucratic.

**2. Remaining concrete defects or omissions**

- **Verification ownership is too diffuse.** Folding the fact-checker role into the `nonfiction_editor` assumes the editor has time and resources to open original sources, verify quotations, and map exact claim locators. Evaluating evidence sufficiency (argument) is not the same as verifying claims (source inspection). The workflow should explicitly mandate that the `nonfiction_editor` (or a fresh `researcher` session) independently open original sources for consequential claims, with coverage recorded in `research/claims.json`. Otherwise, researcher-generated summaries will still be passed off as fact.
- **Review packet defaults still risk contamination.** While `--mode review` excludes handoff and outline, the context packet section says "include brief... then relevant constraints." There is no hard structural block preventing the coordinator from including prior verdicts if they mis-tag. The CLI should generate review packets with a strict manifest that omits `handoff.md` and prior reviews unless explicitly requested with `--include-rationale`. This prevents reviewers from rubber-stamping via inherited justification.
- **Budget enforcement lacks input/tool constraints.** The example `tasks.json` includes `max_rounds` and `max_output_words`, but the context packet section does not demonstrate how `max_input_chars` or `max_tool_calls` are enforced during packet assembly or execution. Without bounded input budgets, agents will pull entire universes into context, collapsing knowledge boundaries. Make these fields validated by the CLI.

**3. Up to three useful acceptance checks**

1. **Source-spot check:** Give the `nonfiction_editor` three claims with citations. Require the report to map each claim to an exact page/line in the original source file. If the report only cites the researcher’s `claims.json` entry, fail the check.
2. **Cold-review contamination test:** Run a developmental edit using `packet --mode review`. Verify the generated packet excludes `handoff.md` and prior reviews. If the reviewer’s output references the drafter’s stated intent or previous findings without a `--include-rationale` flag, the packet is contaminated.
3. **Knowledge boundary audit:** Select one midpoint chapter. Verify that the drafter’s input packet contains zero accepted facts from `canon.json` or character profiles that the POV character could not know at that chronological point, unless the packet explicitly labels it as `author-plan` (not POV-permitted).

Astra’s reconciliation successfully resolved the most dangerous gaps. The system is now ready for a live test on one fiction scene and one sourced nonfiction section. Do not expand the role roster further.
