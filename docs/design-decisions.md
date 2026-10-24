# Studio design decisions

Date: 2026-10-23. Scope: a reusable professional writing environment, not a sample
novel, publishing business backend, or replacement agent runtime.

## Native agents, shared editorial contracts

Codex and OpenCode own execution, delegation, sessions, tools, and permissions.
Their native agent files reference `.studio/agents/` directly. The human author
owns the creative direction; the AI director coordinates bounded assignments.

An early implementation included Python role generation, a consultation client,
and a Codex process launcher. The author clarified that native Codex/OpenCode
integration was wanted, without rebuilding their agent layer. Those components
were removed. The optional `tools/studio.py` now only scaffolds, checks, packages
context, and assembles book files; it has no model or agent execution code.

## Consultation and reconciliation

The design was discussed with the requested models:

- GPT-6 Astra through a Codex subagent: [consultation and reconciliation](../.studio/reviews/2026-10-23/astra-round-1.md).
- Ollama Kimi K3, `kimi-k3:cloud`: [independent proposal](../.studio/reviews/2026-10-23/kimi-k3-round-1.md)
  and [final critique](../.studio/reviews/2026-10-23/kimi-k3-round-2.md).
- Mistral Large V4, resolved to Ollama's official `mistral-large-4:cloud`:
  [independent proposal](../.studio/reviews/2026-10-23/mistral-large-4-round-1.md)
  and [final critique](../.studio/reviews/2026-10-23/mistral-large-4-round-2.md).

Kimi and Mistral received the other model's first proposal, Astra's reconciliation,
and the current operating rules for one final critique round. Reports preserve
their actual responses, including attribution slips, speculative recommendations,
and descriptions of the then-current design. They are consultation artifacts,
not authoritative tool documentation or descriptions of the final implementation.

## Accepted choices

- Direct `{universe}/{series}/{book}` paths, including standalone and nonfiction
  containers. Shared canon and character biographies have one authoritative home.
- Sixteen roles in the catalog; normally only a director, creator, and reviewer
  are active. Dialogue and knowledge tracking are responsibilities within existing
  roles. Acquisitions, nonfiction evidence review, production, and art direction
  cover the broader professional publishing workflow.
- Separate accepted truth, proposed additions, character beliefs, and reader
  disclosures. Track chronological state and cross-book promises with stable IDs.
- One working manuscript with an explicit chapter manifest; snapshot-specific
  reviews and reproducible exports. A source-hash inventory supports recovery and
  review freshness without multiplying ambiguous final drafts.
- Independent initial reviews, one critique round for consequential disputes,
  limited revision attempts, and durable handoffs. A whole-book read remains a
  distinct assignment; scene approvals do not establish cumulative quality.
- Independent source inspection for consequential factual claims. Preserve actual
  evidence, qualifications, and counterevidence; a citation is not verification.
- Voice references, targeted edits, and explicit preservation of deliberate
  departures. Protect interesting choices instead of averaging every sentence.

## Rejected or limited recommendations

No mandatory human approval for every outline, ordinary canon addition, or local
correction. Work continues within the authorized brief; material retcons, unresolved
creative intent, and publication remain meaningful author decisions.

No assumptions that Ollama cloud inference is local/offline, that a paid model is
automatically a better editor, or that assigning different model names guarantees
independence. Model routing is a starting preference to assess with actual work.

No universal scene formula, numerical literary quality score, automatic claim of
publishability, hostile criticism requirement, database, autonomous staff simulation,
or custom orchestration framework. The ledgers are compact references; optional
templates do not all need filling before the first scene.

## Validation and limits

The optional file helper passes **11 behavior tests** covering safe scaffolding,
preservation of shared records, explicit export order, missing/duplicate/path-escape
handling, whole-file packet omissions, review-context separation, malformed records,
and claim-source references. Empty library structure checks pass; no actual book
has been created as part of setup.

OpenCode's native configuration loaded all sixteen specialists with their requested
model routes. The native Kimi canon-keeper and Mistral reader-advocate launches
were exercised on an explicitly synthetic fiction fixture. The reports are saved
under `.studio/reviews/2026-10-23/opencode-*-fixture.md`.

The tested Codex CLI session did not expose a custom-role selector. Native Codex
delegation with an explicit role ID, Astra request, and shared contract was tested
on the synthetic nonfiction fixture. Its independent reviewer found the planted
causation, denominator, missing-response, and generalization errors. See
[the review](../.studio/reviews/2026-10-23/codex-native-nonfiction-fixture.md).
Do not describe a discovered TOML file as proof that a selector was used.

These small fixtures verify useful review behavior and the tested native invocation
paths. They do not benchmark model families, validate a whole book, or establish
publication readiness. Mechanical validation and literary judgment remain distinct.
