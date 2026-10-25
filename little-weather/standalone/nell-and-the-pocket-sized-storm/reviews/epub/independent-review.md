# Independent EPUB production and illustration proof

Reviewer: separate illustration-review agent, 2026-10-25. Verdict: **pass within the coverage below**. No material defects found. This is an archive and Chrome XHTML proof, not a reading-app/device certification or publication approval.

## Snapshot and independence

Reviewed `exports/nell-and-the-pocket-sized-storm.epub`, SHA-256 `5027cc6302965743f55ed9c8e5f69087b0a72ec961093112426002752eb0fa7e`.

Supporting snapshot SHA-256:

- `exports/epub-manifest.json`: `e3db63fd4d73c8177709fa0b89889e376b36cde02219e9dbcbc19d0b43f558fa`.
- `reviews/epub/epubcheck.json`: `81698b2a62dd1907b1cd02044edeb0c10e35bc0a9e8381436cb7b48ebcc281d6`.
- `reviews/epub/browser-proof.json`: `a0a49971430209ab1efc3fdaa4a9744d5a4cf504af9f9802c01b9e85ec171285`.
- `reviews/epub/verification.json`: `455ebb003c300164060b51ecc661d6d5ace0b19747be44513c79a808618b0010`.

I read the applicable instructions, brief, book order, six actual manuscript files, visual style, illustration plan, knowledge boundaries and cast reference. I did not create the text, artwork or EPUB, and did not consult prior editorial verdicts or the handoff. A separate agent supplies procedural independence; no different-model independence is claimed.

## Archive and text checks

Directly inspected the ZIP, container, OPF, navigation, XHTML and CSS. The correct uncompressed `mimetype` is first. The EPUB 3 package declares pre-paginated layout, automatic orientation and no synthetic spreads. Thirty linear spine documents preserve page order; the title remains on story page 1. The library cover is outside the spine and adds no story page.

Independently compared all 293 story paragraphs across all 30 XHTML pages against the six manuscripts in `book.json` order, retaining paragraph order and punctuation: exact match. The prose is real XHTML text. All six chapter links, thirty page targets and the start-reading landmark resolve. All linked local resources and fragments resolve; no script elements or remote CSS dependencies were found. Three font files and their license are embedded.

All recorded current-input hashes and packaged-resource hashes match the inspected manifest. All twelve packaged story-art hashes match the illustration plan and selected local assets, including preserved transparent PNGs. Thus the exact source and individual art hashes are bound by the manifest hash above. Art occurs on pages 2, 4, 6, 9, 12, 15, 17, 19, 23, 24, 27 and 30: two pictures per actual chapter.

The inspected EPUBCheck 5.4.0 report contains zero fatal errors, errors or warnings. I inspected that report; the coordinator ran the validator.

## Actual visual coverage

I inspected the extraction/render scripts: `verify_epub.py` extracts the verified archive into a fresh temporary directory; `proof_epub.mjs` opens those actual XHTML documents in Chrome, awaits document load, fonts and image decoding, then captures 720 × 912 PNGs. All thirty PNG hashes match `verification.json`.

Individually viewed every picture-bearing render: **2, 4, 6, 9, 12, 15, 17, 19, 23, 24, 27, 30**, and all remaining chapter openings: **1, 11, 16, 21, 26**. Chapter 2 opens on the inspected picture page 6. Magnified the chapter labels on 21 and 26; both read completely. This is 17 individually viewed composed pages, with all twelve story illustrations inspected in context. No contact sheet substituted for these views.

The other thirteen pages, **3, 5, 7, 8, 10, 13, 14, 18, 20, 22, 25, 28, 29**, were checked for text, structure and recorded geometry, but were not individually visually inspected. Independently checked all thirty recorded paragraph, heading and folio rectangles: none extend beyond the viewport or overlap another text rectangle. The browser proof records all thirty compositions matching the approved HTML geometry within 0.15 CSS pixels, with fonts loaded and images decoded.

## Image and composition assessment

No observed cast, action, prop-custody, anatomy or disclosure contradiction warrants revision. Nell and Grandma remain recognizable; Grumble's scale changes follow the text. The dog appears after its entrance. The grounded kite preparation on 6 and 23 precedes flight; the mitten is visibly suspended below the kite, occupied on 24 and empty after the reunion on 27. The single rainbow is confined to the final page. No accidental lettering or threatening visual treatment was observed.

Aesthetic judgment: the composed pages sustain a warm, readable read-aloud edition. Page 2's large intimate vignette flows into the kitchen environment on 4. Page 9 uses quiet upper space for clear columns without covering faces. Page 12's isolated figures give the social rupture room; page 15's central ensemble connects two text blocks. The broad garden scenes on 17 and 19 provide communal scale. Page 23's narrow preparation scene leads convincingly into the continuous sunset paintings on 24 and 27, where visible height serves the departure. Page 30's small boot vignette leaves an appropriately quiet finish. Transparent edges integrate with cream paper; full-width scenes use deliberate rectangular transitions. Type, focal crops and folios are clear on the inspected pages, with no observed collisions.

## Accessibility and limits

All twelve narrative alternatives survive in XHTML and describe the depicted scenes. Chapter/page navigation and textual reading order are present. Screen-reader behavior, keyboard interaction, accessibility conformance and the library-cover image were not independently proofed. No Apple Books, Kindle, Kobo or physical-device test was performed. Chrome composition evidence cannot establish reading-system compatibility. Fixed layout requires page zoom for larger text.

Next action: coordinator may deliver this verified EPUB for the author's private reading. No EPUB correction is requested by this review.

## Metadata integration addendum, 2026-10-25

Rechecked the completed manifest, now SHA-256 `82026256e64fea8106b058c4ea9a3246e88ebff473bb4b3815004b7bb78f701e`. Its `validation` field records completed EPUBCheck and package/page proof; `verification_record` and `independent_review` point to the existing reports. Restoring the original pending-validation value and removing these two links reproduces the exact earlier manifest SHA-256 recorded above, confirming that only those three fields changed. The actual EPUB still hashes to `5027cc6302965743f55ed9c8e5f69087b0a72ec961093112426002752eb0fa7e`; all current input and packaged-resource hashes verify. The verification, browser-proof and EPUBCheck report hashes are unchanged. No EPUB, content or resource change occurred. The previous proof coverage and scoped pass carry forward; no rerender was needed or performed.
