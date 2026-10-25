# Final proof: Nell and the Pocket-Sized Storm

Date: 2026-10-25. Assignment: TASK-0004. Reviewer: native copy_editor, GPT-6.1 Sol, high reasoning, fresh context. This is a same-model-family review, not cross-model validation or child testing.

**Verdict: pass for the scoped final proof. No necessary correction remains identified.** This finding applies only to the final hashes below and the stated coverage.

## Inputs and snapshot

Read the root, universe, series, and book AGENTS.md; copy_editor contract; craft standards; brief; style; book.json; both supplied snapshot/manifest records; and the entire manuscript, pages 1–30. Handoff, outline, prior editorial reports, and drafter rationale were withheld. After the initial proof, the coordinator supplied a two-page spoon-custody correction; no developmental report was read.

Final SHA-256 values, computed from disk and checked against all entries in both snapshot/manifest records:

| Path relative to book root | SHA-256 |
| --- | --- |
| brief.md | `46bcf4c0c9e3000f91a2733b3a6bd043586c19726678019a5c9f2631220c4f4b` |
| style.md | `2c05c179cf9aea5196e3c648f063facdcd5a9e60720649cb3b8293a3721cbb8b` |
| book.json | `1dde062b669ca5ae5de7faa07467e5477f5341f7cfdf3375007cc8799dae22af` |
| manuscript/001-story.md | `1b0619f51d42774f6d948388d70e291361f3348bbd832d3bd29edfc7e57e7a7d` |
| production/build.py | `694966067f628f23cb7d36eb6e30eb0aca788022b61a9ebc455676600f6a8976` |
| exports/nell-and-the-pocket-sized-storm.html | `da6b67ea52ee860f0c7fef7b6b9dc604e96db1d6a25737d9569ca77b21ddcede` |
| exports/nell-and-the-pocket-sized-storm.pdf | `737e0332eeaf3d46f3d9495c2bb059c3977eab67964834a59b085b04ab1b7aa0` |

The builder and HTML were hashed, not independently code-reviewed or browser-tested.

## Checks and actual coverage

- Manually copy-proofed the full manuscript for spelling, grammar, punctuation, speaker attribution, names, tense/POV, capitalization, and house style. No definite error remains identified. Nell, Grumble, Grandma, and Mr. Moss are consistent. English double quotation marks and the no-em-dash convention are observed. Intentional fragments, repetitions, sound spellings, and comic wording were preserved.
- Used `pdfinfo` on the actual final PDF: exactly 30 pages, 540 × 684 points (7.5 × 9.5 inches), with no extra cover/front matter.
- Used `pdftotext -layout` and compared every final PDF page against its corresponding manuscript page. All 30 bodies match after whitespace normalization and joining an existing hyphen across a line break. Running header, decorative dots, and correctly numbered footer were checked separately; the full title occurs once, on page 1. No missing, duplicated, substituted, or misplaced story text was detected.
- Page 20's `armchair-` / `sized` line wrap was examined in the rendered PDF and is an ordinary compound-word break, not missing text or a new hyphenation error.
- Used `pdftotext -bbox` on all final pages. No extracted word box extends beyond its page. These checks supplement visual sampling; they cannot prove that every graphical element is unclipped.
- Rendered with `pdftoppm` and inspected images using `view_image`. Unique visual coverage: pages **1, 9, 17, 20, 23, 25, 26, 30**. These include the title, short dialogue, dense sound-effect page, compound wrap, changed passages, late dialogue, and ending. No visible clipping, collisions, illegible glyphs, or footer overlap was found in those samples.

## Revalidation and findings

The first pass used manuscript SHA-256 `6b11cc265c8098447201777129620b4613e4a9129eb9a451cf92429303624d87` and PDF SHA-256 `6c4df9cb31bf5c18ba7cfc8c39f984e54cdb52dcc7d529bf0f182a895b1e38e3`. It independently noticed the spoon-location discontinuity across pages 23–25.

The final text now puts the spoon in Nell's pocket on page 23 and retrieves it on page 25, so running with the kite on page 24 no longer leaves the spoon behind. That issue is resolved. Both changed pages were reread and freshly rendered after the rebuild. All 30 final pages were compared again; text and word-coordinate changes were confined to pages 23 and 25. Earlier visual coverage of the six other sampled pages was retained after their extracted text and coordinates were confirmed unchanged.

No unresolved material findings, optional taste changes, or canon/state/claim proposals are submitted. Citations are not applicable to this fantasy story.

## Limits and next action

The remaining 22 pages were checked for text fidelity and word bounds, not visually inspected. No physical print proof, device-specific reader test, accessibility audit, rights review, or external human/child read-aloud test was performed. This proof does not certify literary quality or universal rendering behavior.

Only this report was written in the repository; extraction and rendering scratch files were confined to `/tmp`. The coordinator can record the scoped proof result against the final snapshot and complete the delivery handoff.
