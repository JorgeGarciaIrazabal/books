# The Ledger of Ashes: public fan edition

Date: 2026-10-27
Role: studio_director
Status: **text editions published; Drama 3 audiobook render in progress; audio not
published**
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

## Audio status (not published)

- A 6 h 23 min Piper draft was rendered from 484 word-exact segments in 602 s.
  It was withheld after ASR (`base.en`) found 3,263 word differences across
  483/484 segments, mostly character names (Ragna heard as Ragnar 385 times,
  Sella as seller, Neri as nary, Ilva as ilver, Tavin as taven/tavern, Kelm as
  helm). It is not on the public site.
- The full Drama 3 render, the documented voice, was started over the same 484
  segments. It is expected to take about 6.5 hours. Its output is in
  `wizarding-world/goblin-wars/the-ledger-of-ashes/exports/narration-drama3/`
  (gitignored) and is not part of this release.
- **No human listened to either audio draft.** The author accepted this limit
  for the planned audio release. Drama 3 output still needs coverage checks and
  chapter assembly before publication.
- Rights: the voice is synthetic Drama 3 using the provisional Kokoro reference;
  the Fish Audio Community License and voice provenance apply. No identifiable
  person is imitated. The work is unofficial fan fiction; no franchise
  distribution right is claimed.

## Deployment

- Text release commit: `8e3fd8685bc491c257af72812c88d3b50378b1af`
  ("Publish The Ledger of Ashes text editions").
- GitHub Pages run
  [40608512713](https://github.com/JorgeGarciaIrazabal/books/actions/runs/40608512713):
  build and deploy succeeded.
- Live URL: https://jorgegarciairazabal.github.io/books/
- Live evidence: `.studio/reviews/goblin-wars-pages-2026-10-27/live-verification.json`.

## Next action

When the Drama 3 render finishes, assemble the 22 chapter MP3s, spot-check the
names and coverage, add `site/audiobook.html` and `site/audio/the-ledger-of-ashes/`,
update the card and manifest, and publish the audio release. Add Books Two and
Three only when written.
