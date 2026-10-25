# Studio workflow

## Minimum useful loop

Brief → one scene/section contract → draft → independent reader/editor response →
targeted revision → canon/evidence delta → handoff. For a quick sketch, the director
may perform planning and drafting sequentially, then request an independent review.
Do not wait for every template to be filled before writing. Empty optional records
are fine. Expand tracking when an actual continuity or research need appears.

## Book checkpoints

| Checkpoint | Evidence needed | Lead and independent check |
| --- | --- | --- |
| brief | Distinct promise/thesis, reader, scope, constraints; assumptions visible | Acquisitions + director |
| structure | Causal/argument progression, character agency, ending/payoff, viable evidence | Architect + developmental/nonfiction editor |
| sample | A representative scene/section proves voice and reader experience | Drafter + reader advocate |
| draft | Ordered chapters, scene/section records, known gaps and new facts | Drafter + canon keeper/researcher |
| development | Whole-book read, prioritized structural findings, resolution/recheck | Developmental/nonfiction editor |
| line-copy | Stable structure, voice preserved, mechanics and citations checked | Line editor then copy editor |
| continuity-evidence | Timeline/knowledge, promises, claims and citations reconciled | Canon keeper + researcher/nonfiction editor |
| production | Complete assembly, metadata/rights, proof on actual export, open issues resolved | Production editor + fresh proofreader |

The coordinator records these in `reviews/gates.json`. Use `revise` when blocked;
use `not-applicable` with a reason. A report identifies an exact source snapshot
(Git commit plus dirty-file hashes, or a SHA-256 inventory), input paths, coverage,
and omissions. A pass expires for changed passages and dependent records. These are
editorial checkpoints, not automatic release permissions. The author can authorize
a scope change or accept a documented editorial exception.

## Work order and return contract

Record one object per active assignment in `tasks.json`:

```json
{
  "id": "TASK-0001",
  "role": "drafter",
  "status": "in-progress",
  "source_snapshot": "canon revision plus SHA-256 inventory or Git commit",
  "inputs": ["brief.md", "style.md", "outline.md"],
  "allowed_writes": ["manuscript/001-opening.md"],
  "deliverable": "Opening scene plus proposed state changes returned to parent",
  "acceptance": ["Established POV", "A costly choice changes the situation"],
  "budget": {"max_rounds": 2, "max_input_chars": 32000, "max_output_words": 2000, "max_tool_calls": 20},
  "dependencies": [],
  "owner": "runtime/session identifier"
}
```

Return: artifact paths; input snapshot; completed criteria; canon/evidence/state
proposals; uncertainties; checks actually run; next recommended action. Subagents
write only assigned files. Parent updates shared ledgers after checking freshness.
Use explicit `blocked`, `done`, or `cancelled`; do not imply background work continues
after a session ends. Resume stale tasks by verifying the owner has stopped.
After two unsuccessful targeted revision attempts, diagnose the premise or test a
short alternative rather than endlessly paraphrasing. If the task budget runs out,
leave an honest partial handoff with completed coverage and the remaining work.
These task budgets are explicit work-order constraints, not a claim that every
runtime mechanically enforces them. The packet utility enforces its character cap;
OpenCode adapters cap model steps at 40. The coordinator tracks tool calls and
revision attempts and reports budget exhaustion. Character counts approximate context
size; they are not exact tokens. Use a larger justified budget for whole-book reading.

## Context packets

`python3 tools/studio.py packet U/S/B --include PATH ...` produces a bounded,
hashed packet for a specific task. Default contents are book instructions, brief,
style, handoff, and outline. Include relevant accepted facts, character profiles,
earlier scene outcomes, and source excerpts explicitly. Do not send an entire
universe or draft by default. The packet is a snapshot, never an authority.

For drafting, distinguish **author-visible future plans** from **POV-permitted
information**. Supply a scene contract with scene ID, purpose, POV, place/time,
incoming state, desire/resistance, turn, outgoing state, permissible disclosures,
forbidden early revelations, and local length/voice guidance. The default packet
does not enforce spoilers; the coordinator must select and label what is included.
Tie important forbidden revelations to knowledge and series-promise IDs so the
drafter does not have to infer the boundary from a broad outline.

For a fresh manuscript review, use `packet --mode review` and explicitly include
the manuscript to assess. This excludes the handoff and planning outline by default.
For an explicitly assigned outline/structure review, include `outline.md` as the
target instead. Assess the proposed causal or argument structure and evidence
feasibility; do not certify prose execution, experienced pacing, or an earned ending
that has not been written. Record `review_target` as `outline` or `manuscript` in
the report and gate. No new role or checkpoint is needed.
Include the brief, declared target, and relevant constraints. Withhold the drafter's rationale and previous verdicts
until after the first assessment. For continuity review, provide accepted canon and
the knowledge ledger. Cross-check a fresh reader's observations after both return.
Whole-book review is a separate assignment: scene passes cannot establish cumulative
pacing or an earned ending. If a manuscript requires staged reading, preserve ordered
notes, assess cumulative effects, and disclose which parts were actually covered.
Record coverage as `read_in_full`, `skimmed`, and `not_assessed` path arrays in
the gate and report. A pass requires that omitted material is explicitly justified,
and an initial reader review must not receive prior findings disguised as context.

## Accepting canon and controlling retcons

1. Drafter records a proposal with fact ID, text, scope, source passage, story-time
   validity, affected entities and books, and whether it changes an existing fact.
2. Canon keeper checks accepted facts, character chronology, knowledge and published
   dependencies. Return contradictions, uncertainty, and a compatible delta.
3. Director integrates compatible details within the brief. Increment
   `universe.json.canon_revision`, update accepted records, preserve provenance and
   append a decision. Mark the proposal accepted with the decision reference.
4. For a retcon, preserve the old fact as superseded with a link; record impact and
   author ruling when required. Never silently rewrite published reader history.

Planning facts may stay proposed across several sessions. A draft can proceed with
a marked assumption if it does not contradict accepted canon. Do not promote every
decorative adjective into a permanent fact. Track details that constrain later work.

## Bounded design discussion

Use only for consequential forks: premise, ending, arc, structure, world rule,
audience promise. The coordinator states the question, constraints, decision criteria,
and budget. Get independent views from available requested models. Share the other
views for one critique round. Synthesize the best-supported choice with consequences
and dissent in `decisions.md`. There is no majority-vote canon. Stop after the
critique round; test the choice in a short sample when taste remains uncertain.

## Series and nonfiction

Before the next book, refresh the series roadmap, resolved promises, published
facts, character boundary states, and the next book's independent reading promise.
Keep planned twists distinct from released facts. Use explicit series book order;
filesystem sorting is not reading order. Track publication order separately from
in-world chronology. New reader entry points need their own spoiler constraints.

For nonfiction, `scenes.json` contains sections, `knowledge.json` tracks reader
prerequisites/disclosures, and threads track questions and promised takeaways.
World rules become subject scope, definitions, methodology, and terminology.
Characters are optional; real people require source-grounded profiles. Researcher
collects evidence; nonfiction editor independently opens original sources to verify
consequential claims and evaluates the argument and whether the evidence actually
supports it. A fresh researcher can do the independent factual check for fiction.
Record claim IDs actually checked, exact locators, omissions, and unresolved support
in research/claims.json. Factual review is not just citation formatting.

## Model routing and artifact boundaries

Use `.studio/roster.json` for each role’s runtime model and effort. The Codex default is GPT-6.1 Sol high; acquisition copy and developmental editing default to medium. Use the acquisitions high override for premise development. The reader advocate uses GPT-6 Sol high so a principal writer has a different-model reader. A fresh session of the same model remains a useful check, with its independence limit disclosed. Untested research, nonfiction, production and art roles retain their previous model families.

OpenCode currently uses explicitly labeled Ollama fallbacks because the connected OpenRouter key has reached its cap. Do not raise account limits, copy credentials or silently switch providers. Preferred OpenRouter routes are recorded in the roster for a later authorized routing update; they are not active. The Ollama OpenAI-compatible endpoint takes `reasoning_effort`, not the native `think` field. Validate a changed control through the runtime instead of trusting a variant label alone.

A scene’s word budget and the allowance for its state delta must be distinct. Keep handoff/process commentary out of manuscript or public-facing copy. Allow enough runtime steps for the assigned reads, writing and validation; a step-limit summary is not manuscript prose. In a review, distinguish definite errors from queries and preferences, and verify a quoted passage and its cited locator before reporting it as evidence.

The author authorized provisional adoption despite incomplete trials. Short feasibility and evidence guards are editorial changes motivated by observed failures; the larger experimental instruction blocks have not passed a full A/B comparison and are not adopted wholesale. See `docs/model-routing.md`.

## Illustrated stories and illustrated editions

At the brief stage, consider whether pictures are part of the reading promise. For children's stories, record the reading format, visual scope and any reversible art assumptions before drafting. Respect explicit text-only preferences and the author's page or image limits.

Use [.studio/skills/illustrated-story/SKILL.md](skills/illustrated-story/SKILL.md) when pictures are part of the requested reading experience, including an illustrated retrofit. Plan text and pictures together for new stories; protect the existing text and snapshot its edition for a retrofit. A chapter, page, scene and spread are distinct units. Set art frequency from the author request, not a universal quota.

Add visual work to the minimum useful loop: narrative brief and scene contracts → page/spread dummy → visual bible and inspected cast/prop reference → scene commissions → selected images → book design/export → independent image and final-page proof. The dummy uses actual text and defines image scale, negative space and edge treatment for scene commissions. Render representative composed pages and assess them together before extending the design across the book. A reference sheet and recurring ornaments do not count as requested scene illustrations.

Art direction owns visual intent, illustrator owns assigned assets and prompt/provenance records, production owns typography/layout/export, and illustration_reviewer owns an independent report. The director keeps shared tasks, integration and handoff. These are specialist responsibilities, not a requirement to start all roles at once. Existing permission and independence boundaries still apply.

Use book-local production/visual-style.md, production/illustration-plan.json, and assets/illustrations/ for selected source art and references. Order remains book.json.chapters. Validate chapter coverage and local paths with the skill helper, but inspect actual images and the actual export to judge narrative consistency, disclosures, crop and readability. Hash text, plan, references, images and layout sources with the output. Recheck any changed asset and its affected pages.

Record an **illustration** checkpoint for selected-image/prose/reference agreement and a **production** checkpoint for the actual illustrated artifact. Each pass states images/pages individually inspected, samples and omissions; a contact sheet or successful build is insufficient. The production review separately assesses the composed edition's aesthetics, including art/text integration and rhythm across pages or spreads, with concrete examples and taste judgments labeled. Collision-free geometry does not establish successful design, and author feedback overrides an earlier aesthetic pass. A revised export requires its own review. Print constraints derive from the actual printer; private digital reading has no automatic print-resolution requirement. Keep prompts, source method, rights limits and generated-art provenance outside the story.

Capture lessons after the edition is reviewed: observed problem, evidence, smallest durable adjustment, and scope. Do not promote one project's art count, visual taste or layout into a universal publishing rule. See [illustrated-story guidance](../docs/illustrated-stories.md).
