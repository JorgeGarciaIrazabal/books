# Post-setup audit and resolution

Independent audits began 2026-10-23; fixes and verification completed 2026-10-24.
Three native Codex reviewers were requested with `gpt-6-astra` and separate scopes.
They did not read the earlier setup consultations. Each saved a report with source
coverage and limitations. Two later hit a usage limit after saving their reports;
the parent verified and integrated the findings without claiming a fresh independent
review of the fixes.

## Reports

- [Native integration](native-integration.md): no confirmed actionable defect in
  the native definitions, shared references, routing, or installed registry checks.
  Account entitlement, inference, and a full book-writing cycle remain outside
  that audit's coverage.
- [Editorial system](editorial-system.md): two instruction conflicts affecting
  independent review. Both corrected.
- [Files and utilities](files-and-utilities.md): six reproduced bugs in the optional
  file helper. All corrected with targeted regression tests.

## Changes made

| Finding | Resolution |
| --- | --- |
| Book-scoped instructions automatically expose handoff/outline to fresh manuscript reviewers | Template, root rules, and shared reviewer contracts now consistently withhold planning rationale and prior verdicts. The coordinator owns shared handoff updates. |
| Structure checkpoint requires reading an outline while reviewer instructions prohibit it | Explicit outline reviews read that outline as their target and report manuscript execution as unassessed. Workflow, specialist contracts, command, and record conventions distinguish outline and manuscript targets. |
| Symlinked exports can overwrite source chapters | Builds reject a symlinked export directory and output/source aliases before writing. |
| Default packet inputs can escape their book via symlinks | Every default input is confined to the book before reading. Explicit additional inputs remain confined to the library. |
| Failed manifest write can leave a partial or mismatched export | Preflight both targets; restore the previous pair on ordinary write failure or remove a new partial output. The manifest remains the last file written. |
| Scaffold rollback can delete an unrelated task's empty folders | Track only directories actually created by this invocation; register the new book after creating its files. |
| Wrong-type JSON manifests cause unhandled attribute errors | Validate object shape before dictionary access and return controlled CLI errors. |
| Packet hashes normalize CRLF rather than identify source bytes | Hash captured file bytes before decoding. Build assembly likewise hashes the bytes used for its output. |

README now makes native Codex/OpenCode startup the default path. Python remains
an optional book-file helper. No agent runner, model proxy, scheduler, new role,
or orchestration layer was added.

## Verification

The original 11 tests passed before changes. Eight new regression cases then
failed on the original utility behavior, reproducing the reported bugs, including
separate partial-build and replacement-build failures. After fixes, **19 tests pass**:

```bash
python3 -m unittest discover -s tests -v
python3 tools/studio.py check
```

All mutation tests use temporary libraries; no real book or canonical story record
was created or modified. The empty-library structural check reports zero books.
Native definition/reference/model consistency and installed OpenCode registry
permissions were also rechecked without inference calls.

Instruction review confirms a clean input path for a fresh manuscript assessment
and an explicit outline-as-target path for the structure checkpoint. No paid
end-to-end writing or independent model re-review was performed after these fixes.
The pre-existing reports describe their original snapshots; this file records
the parent's resolutions rather than editing historical findings into passes.

## Handoff and limits

No confirmed audit finding remains open. Native orchestration remains the intended
architecture. The next useful product exercise is a first real scene or section
through planning, drafting, independent assessment, targeted revision, and handoff.

Ordinary write failures are covered; process termination, power loss, hostile
filesystem races, cross-platform permission differences, and concurrent editing
of build sources were not tested. Verify the recorded output hash after an abrupt
interruption. Structural checks do not establish literary quality or factual truth.
