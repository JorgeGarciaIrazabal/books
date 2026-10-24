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
