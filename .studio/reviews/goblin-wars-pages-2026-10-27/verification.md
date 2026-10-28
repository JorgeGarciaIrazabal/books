# The Ledger of Ashes: public fan edition

Date: 2026-10-27
Role: studio_director
Status: **text editions and Drama 3 audiobook published**
Source snapshot: `a135b26` plus the working tree; ordered chapter inventory
`a624ce350e948890f0cc59cd549d6baca5a85da4fc038b375e044f7661b29c4e`
(22 chapters, 48,850 whitespace-delimited words; reading master SHA-256
`37bdb51ed63c2c7b0e45264d872178b8eb57cdd30df983c2e01c27dd5956a7af`).

## Authorization and scope

- The author asked to publish the Goblin Wars series to GitHub Pages and, when
  told that only Book One is complete, selected Book One in EPUB, PDF and audio.
- The author chose public fan publication. The edition's About page and
  `dc:rights` state that this is unofficial, free fan fiction with no affiliation
  or endorsement by the rights holders. The story text and canon are unchanged.
- Books Two and Three remain roadmap plans. This release contains only
  *The Ledger of Ashes*.
- The author wants Drama 3 for the audiobook and accepted that ASR is not a
  listening review. The full Drama 3 render is running separately and is not part
  of this text release.

## Published text artifacts

| Path | Change |
| --- | --- |
| `wizarding-world/goblin-wars/the-ledger-of-ashes/production/build_epub.py` | Public fan-fiction notice; title page fits one reader screen |
| `wizarding-world/goblin-wars/the-ledger-of-ashes/production/build_pdf.py` | New 248-page reading PDF |
| `publications/the-ledger-of-ashes.epub` | Published EPUB |
| `publications/the-ledger-of-ashes.pdf` | Published PDF |
| `publications/covers/the-ledger-of-ashes.jpg` | Cover extracted from the EPUB |
| `publications/manifest.json` | Fourth book entry |
| `site/index.html` | Fourth card, wider catalogue description |
| `wizarding-world/goblin-wars/**` | Book source and production records |
| `handoff.md`, `tasks.json` | Release record |

Fingerprints:

- EPUB: 146,201 bytes, SHA-256
  `5b9853756cce16485ca786cbecfa1b9097626be26a24eb217cc5b9b05c12ae47`
  (22 chapters; reflowable EPUB 3; title, About, linked contents).
- PDF: 482,483 bytes, SHA-256
  `32a8fbb9bd53f44af01d63ce239aed2c8d79c7f0a6b3709759d82ccd715c81b4`
  (248 pages; title, About, one-page contents, 22 chapters; PDF bookmarks
  and running page numbers).
- Cover: 25,943 bytes, SHA-256
  `0d11420aad02fd6fa31a9fbe54f680213762663f3a1ce2a653ff603835bd3637`
  (720x1080 JPEG from the EPUB title page).

## Verification actually performed

### EPUB

- The builder checks ZIP/XML validity, uncompressed `mimetype` first, package
  metadata, 22 distinct chapters in `book.json` order, chapter/spine/nav order,
  local links, performance-tag exclusion, and paragraph/title fidelity against
  the manuscript. It also proves the embedded cover equals the exported JPEG.
- The site validator re-opened the published EPUB and checked its package,
  spine, `dc:language`, `rendition:layout: reflowable`, cover and hash.
- Browser reader: the title page, About page, contents and Chapter One render in
  Chrome through EPUB.js; Next and a chapter jump were exercised. The title page
  was reduced from two reader screens to one after the first browser pass.

### PDF

- `pdfinfo`: 248 pages, 432x648 pt, no encryption, no JavaScript.
- `pdftotext`: title, About, contents with page numbers, all 22 chapter titles
  and the story text are present. The source story count is 48,747 words by the
  builder's count.
- `pypdf`: 22 outline entries, one per chapter.
- Visual inspection of rendered pages 1-5: title, About, one-page contents,
  Chapter One opening. Fonts are embedded DejaVu Serif/Sans.
- Not performed: PDF/A validation, page-by-page human proof, print colour proof.

### Site

- `python3 -m unittest discover -s tests`: 51 tests pass.
- `python3 tools/build_catalog.py build`: 4 books, 12 publication files, all
  manifest/package/hash/link checks pass.
- Local Chrome/Playwright: 4 cards, 4-book status, no phone horizontal overflow,
  the goblin reader opens the title page and advances to About; no JavaScript
  page errors.
- Live checks on 2026-10-27: HTTP 200 for the catalogue, the new EPUB, PDF and
  cover; the live EPUB/PDF/cover byte sizes and SHA-256 match the manifest; the
  live catalogue has four cards and the goblin reader shows the title and About
  page. No JavaScript errors.
- Not performed: physical phone/tablet, Safari/Firefox, screen-reader pass.

## Audiobook

- The full book was rendered with the documented Drama 3 voice from the 484
  word-exact segments: 22 chapter MP3s, mono 96 kbps at 24 kHz, 5 h 15 min,
  217 MB. A one-shot batch at `max_tokens=2200` hit a Vulkan DAC allocation
  error after three segments; 1400 is stable. The render ran in 20 chunks of
  25 pages (the last nine).
- Nine segments hit the 1400-token cap and were split at sentence boundaries
  and concatenated: pages 4, 44, 136, 213, 268, 305, 311, 333 and 403. The
  repaired pages were re-rendered and checked for the cap again.
- Coverage and chapter hashes pass. An 11-segment ASR spot check covered the
  nine repaired pages plus pages 1 and 484; differences were names, numbers,
  homophones and punctuation, with one inserted article. No words were missing
  from the repaired takes.
- **No human listened to the audiobook.** The public page states the synthetic
  provenance, the coverage check, the 11-segment spot check and the missing
  human listen. The Piper draft from the same segment map remains unpublished.
- Rights: the voice is synthetic Drama 3 using the provisional Kokoro reference;
  the Fish Audio Community License and voice provenance apply. No identifiable
  person is imitated.

## Deployment

- Text release commit: `8e3fd8685bc491c257af72812c88d3b50378b1af`
  ("Publish The Ledger of Ashes text editions"); Pages run
  [40608512713](https://github.com/JorgeGarciaIrazabal/books/actions/runs/40608512713)
  succeeded.
- Audio release commit: `7a0da7dd84362c792abf068293a7f429e5cea46d`
  ("Publish The Ledger of Ashes audiobook"); Pages run
  [40645325596](https://github.com/JorgeGarciaIrazabal/books/actions/runs/40645325596)
  succeeded.
- Live URL: https://jorgegarciairazabal.github.io/books/
- Live checks: four catalogue cards; the goblin reader title/About pages; live
  EPUB/PDF/cover sizes and SHA-256 matching the manifest; the audiobook page has
  22 native audio players, 0 autoplay, all `preload="none"`, no phone horizontal
  overflow and no JavaScript errors. Chapter 1 returns HTTP 200 with
  `Content-Type: audio/mp3`, 10,288,844 bytes, and its SHA-256 matches the
  published chapter manifest. Evidence:
  `.studio/reviews/goblin-wars-pages-2026-10-27/live-verification.json` and
  `live-audio-verification.json`.
- Not performed: physical phone/tablet, Safari/Firefox, screen-reader pass,
  human listening.

## Next action

Listen to chapter 1 and spot-check the names (Ragna, Tavin, Sella, Neri, Dorrik,
Ilva, Merrok, Kelm, Thorn). If the voice is accepted, keep it; otherwise
re-render with a chosen voice. Add Books Two and Three only when written.
