# Native OpenCode fixture validation

Validation complete. The launch succeeded; here is the full accounting.

## Installation validation report

**Launch:** ✅ Success. The `reader_advocate` subagent launched, completed, and returned a report. No further delegation occurred (its adapter denies subagent/edit/shell permissions).

**Actual role:** `reader_advocate` — "Reports independent reader experience, genre satisfaction, and representation risks."

**Configured model used (no override):** `ollama/mistral-large-4:cloud`, per the installed OpenCode adapter `.opencode/agents/reader_advocate.md` (`model: ollama/mistral-large-4:cloud`). Confirmed `active` in the Ollama provider catalog. The subagent self-reported running as `mistral-large-4:cloud`. (Note: the Codex adapter `.codex/agents/reader_advocate.toml` lists `gpt-6-astra`, but that adapter does not govern this OpenCode runtime.)

**Fixture scoped:** `.studio/reviews/2026-10-23/fixtures/fiction.md` only.

## Findings returned by the reader_advocate

1. **Knowledge/continuity defect (error)** — quoting: *"It meant the harbor master had ordered every witness drowned; Mara knew that as surely as she knew her own name. She had never seen the signal before."* Conflicts with FACT-TEST-1 (she first learns the meaning in SC-TEST-4) and the stated reader-knowledge boundary.
2. **Physical-continuity defect (error)** — quoting: *"She gripped the iron rail with her left hand and hauled herself onto the narrow wall."* Conflicts with FACT-TEST-3 (left hand splinted, cannot grip).
3. **Taste, not error** — fragment-heavy rhythm suits the brief's "deliberate clipped voice"; chronology clean against FACT-TEST-2. No change recommended.

It distinguished errors from taste, suggested minimal repairs, and proposed routing the two defects to drafter/canon keeper.

## Citation and contract verification (my check afterward)

- ✅ Both quoted passages match the fixture **verbatim** (fixture lines 15 and 17).
- ✅ Both fact-ID citations (FACT-TEST-1, FACT-TEST-3) are accurate against the fixture's stated facts.
- ✅ Coverage statement present: read only the fixture; no wider repo, no drafter rationale; independence limits stated.
- ⚠️ **Word cap exceeded**: the report runs ~430 words against the ≤350 ceiling.
- ⚠️ Minor: the first suggested repair for Finding 1 (keeping the narrated meaning while cutting "Mara knew that…") would still leak the meaning to the reader, violating the fixture's reader-knowledge boundary; its alternative (defer the reveal to SC-TEST-4) does fully resolve it. A loose sentence-fragment count in Finding 3 is framed as taste only.

## Unresolved issues / next action

- None blocking. The adapter installation, configured model dispatch, citation anchoring, and error-vs-taste discipline all check out on this fixture.
- If strict adherence to word caps matters for future installs, note the overflow; otherwise the validation passes with the flagged nits.
- No files were created, edited, or handoffs updated, per your instruction. No other specialists were engaged.
