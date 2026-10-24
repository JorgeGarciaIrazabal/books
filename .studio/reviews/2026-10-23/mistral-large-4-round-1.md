# mistral-large-4:cloud: independent design consultation

# Publishing-Studio Design Consultation

**Scope:** Greenfield repo for AI-assisted book production: fiction, nonfiction, series, shared universes. Path invariant: `{universe}/{series}/{book}/` at root. Two runtimes: Codex CLI 0.163 (agent definitions targeting GPT-6 Astra) and OpenCode v2.1 (Ollama Mistral Large 4 + Kimi K3). Markdown as source of truth.

---

## 1. Specialist roster (14 agents)

Models collaborate; humans decide. Every agent is a *role with a contract*, not a persona with autonomy.

| # | Agent | Runtime | Core role | Distinct output |
|---|-------|---------|-----------|----------------|
| 1 | **Creative Director (human-only)** | — | Owns vision, approves canon | Decisions logged in `decisions.md` |
| 2 | **Canon Keeper** | Both | Maintains canon bible, flags drift | `canon/` diffs, drift reports |
| 3 | **Story Architect** | Codex (Astra) | Structure: acts, promises, payoffs | `structure/outline.md`, beat sheets |
| 4 | **Scene Writer** | OpenCode (Mistral/Kimi) | Drafts prose to outline | Chapter drafts in `drafts/` |
| 5 | **Prose Stylist** | OpenCode | Voice, rhythm, line-level polish | Style pass notes + revised draft |
| 6 | **Continuity Editor** | Both | Timeline, character consistency, cause/effect | `continuity/timeline.md`, error log |
| 7 | **Character Psychologist** | Codex | Motivation, arc coherence, POV integrity | Character sheets, arc audits |
| 8 | **Researcher** | Codex | Evidence gathering, citation discipline | `research/sources.md` with provenance |
| 9 | **Fact-Checker / Sensitivity Reader** | OpenCode | Accuracy + representation review | Issue list with severity |
| 10 | **Dialogue Specialist** | OpenCode | Voice distinctiveness, subtext | Dialogue pass report |
| 11 | **Series Architect** | Codex | Cross-book continuity, universe rules | `series/` bible, escalation map |
| 12 | **Cover/Copywriter (metadata)** | OpenCode | Blurbs, keywords, positioning | `marketing/` copy variants |
| 13 | **Dev Editor (independent)** | Codex, cold context | Holistic critique, no drafting memory | `reviews/dev-{date}.md` |
| 14 | **Production Editor** | OpenCode | Mechanics, formatting, manuscript prep | Clean manuscript, style sheet |

**Key design choices:**
- Drafting runs on OpenCode (local models = cheap iteration); structure, canon, and independent review on Astra (stronger reasoning, paid per use — spend where judgment matters).
- Dev Editor gets **cold context** (fresh eyes, only manuscript + brief) to avoid rubber-stamping.
- No agent merges to git without a human PR review. Agents open branches; humans merge.

---

## 2. Artifact tree

```
{universe}/
  universe-bible.md          # rules, magic/tech constraints, tone, themes
  timeline-master.md         # canonical chronology across all series
  glossary.md                # terms, names, pronunciation
  spoiler-policy.md          # who may see what (see below)
  {series}/
    series-bible.md          # premise, arc across books, escalation
    book-promises.md         # genre contract: what the series owes readers
    {book}/
      brief.md               # premise, POV, tone, comps, word target
      outline.md             # act/beak structure
      characters/
        {name}.md            # sheet: want/need/fear/secret/arc/voice notes
      plot/
        beats.md             # scene-level, linked to outline
        promises-payoffs.md  # setup → payoff ledger
      research/
        sources.md           # claim → source → confidence → used-in
        open-questions.md
      continuity/
        timeline.md          # book-local chronology
        state-tracking.md    # who knows what, where, when (knowledge matrix)
      drafts/vNN/            # immutable versioned drafts
      reviews/               # dev, continuity, sensitivity reports
      decisions.md           # human rulings, dated, immutable
      style-sheet.md
      manuscript/            # production output
```

**Spoiler boundaries are structural, not social.** The knowledge matrix (`state-tracking.md`) tracks *in-world* knowledge per character per chapter — this doubles as the anti-spoiler mechanism: the Scene Writer's prompt includes only knowledge available to the POV character at that point. Universe-level spoilers live in `series-bible.md` and are never injected into drafting context for early books. Nonfiction adaptation: replace `plot/` with `argument/` (thesis, evidence map, counterarguments) and `research/` stays identical — the evidence discipline transfers directly.

---

## 3. Quality workflow

**Pipeline per book:** Brief → Outline (Architect, human-approved) → Beats → Draft (Scene Writer + Stylist loop) → Continuity audit → Research/Fact-check (parallel) → Dev Edit (cold, independent) → Revision → Production.

**Canon acceptance is a gate, not a vibe:**
- Three tiers: **Draft** (agent output, cheap to change) → **Book canon** (human-approved, merged to main) → **Universe canon** (requires Canon Keeper sign-off *and* human approval; changes here trigger a drift report across all dependent books).
- Every canon change is a dated entry in `decisions.md`. No silent edits — history is append-only.

**Versioning:** drafts are immutable snapshots (`v01`, `v02`…). Never overwrite. Reviews reference a specific draft version. Git tags at canon-acceptance milestones.

**Independent review matters because models agree with each other.** Same-family models share blind spots; cross-model review (Astra dev edit on Mistral/Kimi draft) is the cheapest insurance.

---

## 4. Concurrency, handoffs, bounded debate

- **Handoffs are files, not conversations.** An agent's "done" state is a written artifact + a status line in the book's `workflow.md` (todo/in-progress/blocked/awaiting-human). No agent waits on another agent's chat memory.
- **Locking:** one writer per file at a time (`locks/` directory with owner + timestamp; stale locks expire). Parallel work happens on *different* files (e.g., Researcher and Dialogue Specialist concurrently).
- **Bounded debate:** for genuine creative disputes, run a **2-round, 2-model debate** — Astra argues position A, Mistral/Kimi argues position B, one round each, then a human ruling recorded in `decisions.md`. Hard cap: no third round. Debate is for decisions with real forks (structure, ending), not for prose polish. This is where cross-model disagreement is *useful*; unbounded debate is where it becomes expensive noise.
- **Models are not staff.** They have no memory between sessions beyond what's in the repo, no ownership, no initiative. Treat every output as a draft from a very fast, very confident junior collaborator.

---

## 5. Starter path — and what not to build

**Week 1, minimal:**
1. Create one universe, one series, one book. Write `brief.md` and `universe-bible.md` by hand (or with one agent session).
2. Define **3 agents only**: Story Architect, Scene Writer, Continuity Editor (as Markdown files with role, inputs, outputs, constraints — one page each, portable across Codex and OpenCode).
3. Establish `decisions.md` and the draft-versioning rule.
4. Draft one chapter end-to-end. Learn where the seams hurt.

**Explicitly do not build yet:** automation scripts, CI checks, agent orchestration, knowledge graphs, databases, prompt libraries, multi-agent pipelines. Add each only when a repeated manual pain justifies it, and prefer a shell script + Markdown over a framework.

**Nonfiction from day one is fine:** the same skeleton works — `argument/` replaces `plot/`, and the Researcher/Fact-Checker pair carries more weight. Don't bolt fiction tooling onto nonfiction later; keep the slots generic ("structure," "evidence") from the start.

**Critical notes:**
- The `{universe}/{series}/{book}` invariant must be enforced by convention + a lint script (a 10-line check that every book dir has `brief.md`). Don't build a CMS.
- Portable Markdown agent definitions: keep them runtime-agnostic (role/inputs/outputs/constraints), with a thin adapter per runtime. Don't write Codex-specific and OpenCode-specific duplicates of the same role.
- The knowledge matrix is your highest-leverage artifact — it prevents spoilers, continuity errors, and retcons simultaneously. Invest there early.
- Measure: if a chapter takes more human hours than writing it yourself, the process is overengineered. Tune agent contracts, not headcount.

**Where I'd expect other consultants to differ:** roster size (I'd defend 14 as a ceiling, not a starting set), which runtime gets which role (I put judgment-heavy review on Astra; another may argue local models suffice), and how much structure to impose before the first draft. My position: structure artifacts are cheap and prevent expensive mid-draft surgery; under-structuring is the costlier failure mode.
