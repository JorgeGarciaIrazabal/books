# Handoff — provisional adoption complete

The author explicitly accepted the incomplete tests and authorized the recommended
model assignments and best-supported instruction updates. Implementation,
documentation, and local verification are complete. No further experiment is
running or queued in the task ledger. No commit or publication was made.

## Adopted behavior

Codex defaults and principal creative roles use GPT-6.1 Sol high. Developmental
editing and acquisitions copy use GPT-6.1 Sol medium; premise development has an
explicit high-effort task override. GPT-6 Sol high supplies the independent reader.
Research, nonfiction, production, and art retain their untested Astra assignments.
The task override is coordinator guidance, not an automatic change to a running
agent; the coordinator must select the matching effort explicitly.

OpenCode retains working Ollama routes with explicit high effort. The preferred
Sol OpenRouter route is recorded but inactive because a native probe returned
HTTP 403 for the connected key's spending cap. The active Mistral drafter receives
a Kimi reader response. No credentials, account limits, or machine-wide settings
were changed. Correct compatible-endpoint controls use `reasoning_effort`.

Concise shared rules strengthen planning feasibility, quotation/locator checks,
scene-contract checks, source-packet selection, and separation of manuscript prose
from process notes. The longer experimental instruction packages were not adopted
wholesale. Same-model editor independence limits remain explicit.

## Validation and limits

- Parsed all 16 Codex definitions; model and effort match the roster. Every other
  native Codex setting matches the pre-adoption snapshot.
- Queried the native OpenCode agent registry with the explicit project-directory
  header. All 16 studio roles resolve to the intended model/variant, mode and
  40-step cap. Existing reviewer edit/shell/delegation denials are preserved.
  `opencode debug agents` initially queried the home directory and returned empty;
  this was resolved by the project-scoped API check, without inference.
- `python3 -m unittest discover -s tests -v`: all 19 passed.
- `python3 tools/studio.py check`: one book, zero structural errors. The benchmark
  book remains a scaffold without source chapters; no manuscript quality claim.
- `git diff --check`: passed.
- The instruction experiment closed with 15 complete primary candidates and one
  valid peer review; one malformed peer response remains invalid. Missing work is
  cancelled. There is no complete aggregate A/B adoption verdict. Original cloud
  effort comparisons remain withdrawn and corrected preflight records separate.
- Independent adoption-audit and documentation workers reached a usage limit.
  Their incomplete work was not treated as a completed audit. The coordinator
  finished the documentation and technical validation; see `validation.json`.
- No successful preferred OpenRouter Sol inference is claimed. Availability and
  account quota remain runtime constraints.

`before.json` preserves the live pre-adoption content and hashes. `after.json`
records changed live-file hashes. `validation.json` records per-role checks.
The experiment's own frozen current/proposed snapshots remain historical inputs.

## Exact live adoption paths

- `.codex/agents/acquisitions_editor.toml`
- `.codex/agents/canon_keeper.toml`
- `.codex/agents/character_director.toml`
- `.codex/agents/copy_editor.toml`
- `.codex/agents/developmental_editor.toml`
- `.codex/agents/drafter.toml`
- `.codex/agents/line_editor.toml`
- `.codex/agents/reader_advocate.toml`
- `.codex/agents/series_showrunner.toml`
- `.codex/agents/story_architect.toml`
- `.codex/agents/studio_director.toml`
- `.codex/agents/universe_architect.toml`
- `.codex/config.toml`
- `.opencode/agents/acquisitions_editor.md`
- `.opencode/agents/art_director.md`
- `.opencode/agents/canon_keeper.md`
- `.opencode/agents/character_director.md`
- `.opencode/agents/copy_editor.md`
- `.opencode/agents/developmental_editor.md`
- `.opencode/agents/drafter.md`
- `.opencode/agents/line_editor.md`
- `.opencode/agents/nonfiction_editor.md`
- `.opencode/agents/production_editor.md`
- `.opencode/agents/reader_advocate.md`
- `.opencode/agents/researcher.md`
- `.opencode/agents/series_showrunner.md`
- `.opencode/agents/story_architect.md`
- `.opencode/agents/studio_director.md`
- `.opencode/agents/universe_architect.md`
- `.studio/agents/canon_keeper.md`
- `.studio/agents/drafter.md`
- `.studio/agents/story_architect.md`
- `.studio/agents/studio_director.md`
- `.studio/roster.json`
- `.studio/workflow.md`
- `AGENTS.md`
- `README.md`
- `docs/model-routing.md`
- `docs/tooling.md`
- `opencode.json`

Additional closure edits:

- `.studio/experiments/instruction-ablation-v1/handoff.md`
- `.studio/experiments/instruction-ablation-v1/run-manifest.json`
- `.studio/experiments/instruction-ablation-v1/tasks.json`
- `.studio/experiments/instruction-ablation-v1/runtime/live-jobs.json`

The adoption records in this directory and `docs/model-routing.md` are new.
Earlier benchmark outputs, control corrections, and the book scaffold are preserved.

## Next action

Start a fresh Codex session at the repository root to use the new defaults for
normal book work; use the named role selector when available. OpenCode can use its
loaded Ollama fallbacks now. A future provider change needs a successful native
route probe and synchronized roster/native definitions; do not raise an account
limit to achieve it. If comparative testing resumes, create a separate continuation
snapshot rather than presenting this incomplete experiment as complete.
