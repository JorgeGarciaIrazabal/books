# Illustrated stories in Book Studio

Use the [illustrated-story skill](../.studio/skills/illustrated-story/SKILL.md) to create a story with pictures or add them to an existing manuscript. It complements the normal editorial workflow rather than replacing prose development. An illustrated chapter book may use a few pictures per chapter; a picture book may build meaning across spreads. The author's edition and image count determine the work.

## Responsibilities and records

| Responsibility | Role | Evidence |
| --- | --- | --- |
| Visual direction and scene commission | art_director | Visual bible, cast/prop reference, page/spread dummy and illustration plan |
| Reference-led scene images | illustrator | Selected images, full prompts, reference/asset hashes, provenance and proposed alt text |
| Type, page design and export | production_editor | Actual illustrated edition and source/output manifest |
| Independent visual proof | illustration_reviewer | Images compared with prose/references; final picture-bearing pages inspected with exact coverage |
| Integration and durable lessons | studio_director | Task ownership, resolved findings, scoped gates and handoff |

The two new role definitions reuse existing model families and are marked unbenchmarked. Their language-model assignment does not name the image-generation model. Native definitions become available according to the runtime's discovery/session behavior; writing a definition does not start a worker. If the current runtime has no selector for a new role, assign the exact contract to an available native child with an explicitly recorded supported model/effort, or disclose the limitation. Do not claim an unavailable selector was used.

Use `production/visual-style.md` and `production/illustration-plan.json`; templates are provided for new books. Keep source assets locally, commonly under `assets/illustrations/`, and generated editions under `exports/`. Read the [record reference](../.studio/skills/illustrated-story/references/plan.md) for fields and the validator. The ordinary workspace helper remains dependency-free and does not run image models.

## What the proof establishes

Art review compares the depicted moment with prose: identities, scale, possessions, action, place, light, mood and reader knowledge. A reference sheet does not prove the scene images followed it. View selected images individually; use thumbnails additionally to compare the book's cohesion and rhythm. Record actual files/hashes and any omitted scope.

Commission art for the actual text composition, including subject scale, usable negative space and edge/background treatment. Render representative composed pages before commissioning the whole set, and compare their sequence or intended spreads at reading size. This can expose art that feels pasted onto the page while a change remains inexpensive. Rectangular panels can work; neither banning them nor requiring a number of layout types establishes successful integration.

Layout proof reads the actual exported artifact. Inspect every picture-bearing page, chapter breaks, text legibility, focal crops, image/text/gutter boundaries, missing images, page count and source-text fidelity. Check accessibility metadata in the intended format or state that it remains unverified. Successful conversion and image existence are mechanical evidence, not certificates of artistic quality or rights clearance. Give aesthetic judgment its own explicit assessment: image/text integration, edge transitions, scale, negative space and rhythm across the composed sequence. Cite examples and distinguish defects from taste. Author feedback overrides an earlier aesthetic pass; a changed export needs review of its own.

Native image pixels and placed size determine effective PPI. A digital reading edition does not automatically need a printer's resolution/color/bleed setup. A print edition needs the selected printer's actual specifications and a proof of that output. Avoid describing an untested digital PDF as print-ready.

## Learning from a completed edition

Keep a short evidence log with the observed failure or success, affected asset/page, intervention, recheck and appropriate scope. A character drifting between images supports using inspected references on every call. A text collision supports a layout correction and export proof. Neither observation establishes a universal art count, trim, type size or style. Link actual findings before describing a process adjustment as learned; mark an untested idea as a proposal.

For the Nell illustration task, the author requested one or two pictures per chapter after receiving a text-led 30-page edition. This establishes the need to reconcile chapters with page count, add real scene art rather than count existing ornaments, preserve the earlier edition, and reproof the changed export. Final case-specific outcomes belong in that book's review/handoff records; this guide does not claim an unperformed test or completed image inspection.

During generation, Nell's page-6 picture included the reference-sheet dog even though the dog enters on page 16. The coordinator detected it by viewing the scene and requested a localized removal, preserving the other art. This supports an explicit included/excluded cast in scene prompts and a background continuity check. The repaired asset was individually inspected and its final page proofed. The original rejected asset is retained under the book’s assets/iterations/. An edit request alone would not establish success.

The completed Nell run also exposed duplicate faces on two cloudpoints, a missing kite tether needed by the following scene, and provisional alt text that did not match the final picture. These were corrected and rechecked. The [book’s observed lessons](../little-weather/standalone/nell-and-the-pocket-sized-storm/reviews/illustrated/lessons.md) links each intervention to its evidence and appropriate scope. The illustrated edition retains all 30 story page bodies, six chapters, twelve pictures and 16.8 pt type. These counts describe this edition, not defaults for every new story.

The author later rejected Nell's repeated rectangular pictures at the bottom of the pages as artificial, despite the [earlier visual pass](../little-weather/standalone/nell-and-the-pocket-sized-storm/reviews/illustrated/visual-review.md). This is direct evidence that the edition missed the author's aesthetic intent; the checks for correct assets and collision-free placement did not settle integration or rhythm. The bounded correction is to commission for the page composition, compare early composed pages, and assess the final sequence aesthetically. It does not establish a universal ban on rectangular art. The [book-local lessons](../little-weather/standalone/nell-and-the-pocket-sized-storm/reviews/illustrated/lessons.md) retain the case evidence. The replacement received a [snapshot-specific review of all thirty actual pages](../little-weather/standalone/nell-and-the-pocket-sized-storm/reviews/redesign/final-review.md), with aesthetic assessment separate from mechanics. That editorial result does not presume author acceptance.
