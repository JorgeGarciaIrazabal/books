# Record conventions and examples

The scaffold uses JSON objects with `schema_version: 1` and a named record array.
Every record needs a unique, nonempty `id` within its file. Keep meaningful
explanations in Markdown; the ledgers track references and state. The examples below
are **illustrative, not canon**. Add fields as an actual story needs them.

The checker validates record-array shape and IDs, chapter order and basic paths,
and source references in claims. The richer fields below are an editorial contract,
not a claim that every relation is automatically enforced. Do not equate valid JSON
with a valid story or verified evidence.

## Canon and chronology

`{universe}/canon.json` has `facts`; `{universe}/timeline.json` has `events`.
Qualified references include the owning path when crossing books or universes.
Dates can remain a range or relative order rather than acquiring false precision.

```json
{
  "id": "FACT-0001",
  "text": "The eastern crossing closes at the first winter storm.",
  "status": "accepted",
  "truth_type": "objective",
  "scope": "glass-sea",
  "valid_story_time": "from Year 14 onward",
  "provenance": [{"path": "glass-sea/tidebound/book-01/manuscript/001-opening.md", "locator": "scene SC-0001"}],
  "decision": "glass-sea/decisions.md#dec-0001",
  "accepted_revision": 1,
  "supersedes": null
}
```

Use `proposed`, `accepted`, or `superseded`. Put unreliable beliefs in an attributed
record rather than objective facts. Material retcons preserve superseded records.
Increment `universe.json.canon_revision` on acceptance; log the decision and all
affected records together. With Git, a single commit can make that group recoverable.
Without Git, preserve the before-state in a review/decision attachment before a
multi-file canon update; record incomplete updates in the handoff if interrupted.

An event record needs ID, time/range, ordering dependencies, participants, place,
consequences, and source. A proposal in `book/canon/proposals.json` additionally
needs `status`, `affected_paths`, `changes_existing_fact`, and a decision reference
on acceptance/rejection. A proposal is not accepted merely because it exists in prose.

## Scenes, knowledge, and promises

```json
{
  "id": "SC-0001",
  "chapter": "manuscript/001-opening.md",
  "kind": "scene",
  "pov": "CHAR-0001",
  "story_time": "Year 14, before the first storm",
  "depends_on": [],
  "incoming_state": "The cartographer has an intact chart and trusts the harbor master.",
  "turn": "She burns the chart to protect the crossing's location.",
  "outgoing_state": "The chart is lost; the harbor master now suspects her.",
  "canon_proposals": ["PROP-0001"],
  "promises": ["THR-0001"]
}
```

Scenes follow narrative order in the ledger; story-time order may differ. Do not
overwrite earlier boundary states with the newest profile. For nonfiction use
`kind: section`, a reader question, claim IDs, prerequisites, and changed understanding.

```json
{
  "id": "KNOW-0001",
  "subject": "CHAR-0001",
  "fact_ref": "glass-sea/canon.json#FACT-0001",
  "learned_in": "SC-0001",
  "how": "A direct warning from the ferryman",
  "belief": "true",
  "reader_revealed_in": "SC-0003",
  "allowed_from": "SC-0001",
  "source": "manuscript/001-opening.md"
}
```

Knowledge records distinguish truth, belief, evidence available to the character,
and reader disclosure. Use `subject: reader` for reader-only information or
nonfiction prerequisites. Future-planning notes must not leak into early dialogue.

Local `threads.json` and series `promises.json` use stable IDs, setup source,
reader expectation, intended payoff window, dependencies, status (planned, planted,
paid, deferred, abandoned), actual resolution, and a reason for deferral/abandonment.
Cross-book references link local threads to the series promise's owning file.

## Research sources and claims

```json
{
  "id": "SRC-0001",
  "title": "Inspected source title",
  "author": "Source author or institution",
  "date": "YYYY-MM-DD or documented unknown",
  "url_or_path": "https://example.org/primary-source",
  "accessed": "YYYY-MM-DD",
  "type": "primary",
  "inspection": "Read the named passage and relevant methods",
  "limitations": "Record actual scope, uncertainty, conflicts, and source quality"
}
```

```json
{
  "id": "CLM-0001",
  "text": "The precise claim made in the manuscript",
  "used_in": ["manuscript/002-evidence.md"],
  "status": "unverified",
  "evidence": [{"source_id": "SRC-0001", "locator": "page 12, table 3", "supports": "Specify which part and within what scope"}],
  "counterevidence": [],
  "inference": "None, or state the reasoning beyond the source",
  "verified_by": null,
  "verified_snapshot": null
}
```

Use `unverified`, `verified`, `disputed`, or `unsupported`. Set verified only after
an independent check of the actual passage. A verified claim must have source IDs
and locators; the checker catches missing links but cannot inspect their truth.
Record contradictory sources rather than deleting inconvenient evidence.

## Editorial findings and checkpoints

```json
{
  "id": "ISSUE-0001",
  "role": "canon_keeper",
  "snapshot": "SHA-256 inventory or exact Git commit with dirty hashes",
  "location": "manuscript/002-arrival.md, SC-0003",
  "severity": "major",
  "category": "error",
  "evidence": "A cited passage reveals information before the character learns it.",
  "impact": "Undermines the mystery and character plausibility.",
  "suggestion": "Remove the premature assertion or establish how she learned it.",
  "status": "open",
  "resolution": null,
  "rechecked_by": null
}
```

Issue status: open, in-progress, resolved, accepted-exception, or dismissed-with-reason.
A gate record needs ID, checkpoint, `review_target` (outline/manuscript/export),
`status` (pass/revise/not-applicable), reviewer,
snapshot, report path, coverage, open finding IDs, and rationale. A broad report on
three chapters does not cover a whole book. After substantive edits, explicitly
recheck affected findings and gates. Record proof coverage against the actual export.

Use a structured coverage object, for example
`{"read_in_full": ["manuscript/001-opening.md"], "skimmed": [], "not_assessed": []}`.
List omitted chapters honestly. Empty omission lists do not prove a full read;
the report and actual review assignment must support the claimed coverage.
