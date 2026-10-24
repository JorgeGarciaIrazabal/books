# Native OpenCode fixture validation

Validation complete. The child launched, inspected only the fixture, and its citations check out against the file (verified post-run; nothing was edited, created, or handed off).

## Child role/model actually used
- **Role:** `canon_keeper` (installed project subagent from `.opencode/agents/canon_keeper.md` — read-only, delegation denied). No generic-role substitution; I passed no model override.
- **Model:** project config declares `ollama/kimi-k3:cloud`; the child self-reported `kimi-k3:cloud`. Consistent.

## Findings returned (3/3, scope: fixture only)
1. **FACT-TEST-1 / FACT-TEST-2 — character-knowledge violation:** Mara cannot know the signal's meaning in SC-TEST-2 (she first learns it in SC-TEST-4), yet the text says *"It meant the harbor master had ordered every witness drowned; Mara knew that…"* — and *"She had never seen the signal before"* sharpens rather than cures it.
2. **Reader-disclosure leak:** the same sentence reveals the signal's meaning to the reader ahead of the permitted disclosure point ("Reader knowledge: the reader also has not learned the sealed signal's meaning").
3. **FACT-TEST-3 — physical-state violation:** her splinted, non-gripping left hand "gripped the iron rail… and hauled herself onto the narrow wall" with no healing event.

All three planted defects found, all quoted passages verbatim-accurate, no out-of-scope reading reported or observed.

## Launch limitations
- The subagent tool response does not itself expose the running model ID; attribution rests on the project agent config plus the child's self-report. Coordinator and child run on the same model (kimi-k3:cloud), so per AGENTS.md this is a single-model session — the "independent review" is procedural only (fresh child session, no priming: the fixture path was the only input given, and I did not read the fixture contents until after the child returned).
- Minor tooling note: the fixtures live under hidden directory `.studio/`, so a default glob missed them; `hidden: true` was required. No functional blocker.

## State
No files edited, no books created, no handoffs updated. Next action: none required — installation validation passed (subagent registry, role/model binding, file access, and read-only constraint all behaved as configured).
