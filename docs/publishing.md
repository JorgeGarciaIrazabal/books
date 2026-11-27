# Publishing to GitHub Pages

This guide covers how the public library site at
`https://JorgeGarciaIrazabal.github.io/books/` is assembled, checked, and
deployed, and how to add or update an edition.

## What lives where

| Path | Role |
| --- | --- |
| `site/` | Website sources: `index.html` (catalog), `reader.html` (browser EPUB reader), styles, scripts, icon, and the vendored reader libraries in `site/assets/vendor/`. |
| `publications/` | The tracked publication artifacts (`.epub`, `.pdf`), the derived cover images in `publications/covers/`, and `manifest.json` with byte sizes, sha256 hashes, and studio source paths for every file. |
| `narration/` | Optional read-aloud packages: `manifest.json` plus `{book-id}/narration.json` and `{book-id}/page-NN.mp3`. Never part of the EPUB or PDF. |
| `tools/narration.py` | Packs page audio into `narration/` and validates scripts, hashes and tag exclusion. |
| `tools/build_catalog.py` | Build tool: validates the manifest and the actual artifact packages, assembles `_site/` from `site/` and `publications/` only, and checks every URL in the output. |
| `tests/test_catalog.py` | Automated checks for manifest and artifact integrity, EPUB package behavior, vendored library pinning, and subpath-safe output. |
| `.github/workflows/pages.yml` | GitHub Pages deployment workflow. |
| `_site/` | Generated output (gitignored). Never edit or commit it; rebuild instead. |

The website is deliberately a static, buildless front end: no server, no
runtime CDN, no downloaded fonts. The only generated file is `catalog.json`,
written by the build tool from `publications/manifest.json`.

## Responsive presentation

The catalog and reader are styled in three deliberate bands:

| Band | Catalog | Reader |
| --- | --- | --- |
| Phone (`<600px`) | one compact card per book; a 100px cover plate beside the details | adaptive text view for fixed-layout books; compact header, icon pager buttons, contents drawer |
| Tablet (`600–1023px`) | two cards per row | portrait keeps the illustrated page; landscape uses the adaptive text view; contents drawer |
| Desktop (`>=1024px`) | three cards per row, `76rem` maximum | persistent contents rail at wide widths; page view at 1440px, capped text measure when selected |

- Interactive controls use at least a 44×44px target. Search text is 16px so
  iOS does not zoom the page on focus.
- Fixed-layout books have two reading views. **Text** reflows the book's own page
  documents and illustrations into a continuous scroll with a page-aware status,
  contents jumps, saved section and scroll position, and 90–170% text sizing.
  **Pages** is the original illustrated layout, still fitted to its native
  720:912 page ratio.
- The illustrated page view measures the rendered page body and resizes the
  frame to that aspect ratio, so illustrations are neither cropped nor
  left-anchored in a wide white panel.
- The text view is the default on phones, phone landscape, tablet landscape, and
  short landscape laptops up to 1399×820. Tablet portrait and a 1440px desktop
  keep the illustrated page by default. The `Text` / `Pages` header button
  switches views at any size and remembers the choice per book.
- The text view uses the EPUB.js archive already in memory, so it adds no second
  download. Its illustrations load lazily when they approach the viewport, with
  their intended aspect ratios reserved to avoid scroll jumps. It reads the
  `.story` paragraphs, `.chapter-heading`, and `figure img` elements used by the
  studio's fixed-layout exports; a fixed-layout EPUB with a different internal
  structure would need an adapter.
- The phone reader keeps one header row for the illustrated page view; the text
  view adds a slim text-size row. Title flexing keeps the header at two rows even
  at 320px.
- Reflowable books start at 115% on phones (18.4px from a 16px base), 110% on
  tablets (17.6px), and 100% on desktop (16px), within the same 90–170% controls.
  They are capped at `46rem` for a comfortable line length. The progress bar uses
  the EPUB spine index plus the current page within the section when EPUB.js has
  not generated location percentages.
- Safe-area insets, `100dvh`, reduced-motion, and hover-only effects are
  handled in CSS.

These bands were checked with headless Chrome at 320×640, 390×844, 844×390,
768×1024, 1024×768, 1280×800, 1366×768, and 1440×900, including all three books.
That is emulated viewport coverage, not a physical-device or cross-browser
certification.

## Read-aloud narration

Narration is a separate layer. The tagged script, cast and render record live in
the book at `production/narration/`; only the finished mono MP3s and two small
manifests live in `narration/`. The manuscript, the export, the EPUB and the PDF
never contain a performance tag, and the build fails if one is found.

| Path | Role |
| --- | --- |
| `production/narration/script.md` | Tagged script, one block per story page |
| `production/narration/cast.json` | Voices, reference clips, transcripts, provenance, licences |
| `production/narration/render.json` | Engine, model hash, seed, settings, per-page hashes |
| `narration/manifest.json` | Public index: book id, pages, seconds, credit, file hashes |
| `narration/<book-id>/narration.json` | Reader manifest: page to MP3, durations |
| `narration/<book-id>/page-NN.mp3` | 96 kbps mono page audio |

Add or refresh a package after rendering the book's pages:

```sh
python3 tools/narration.py pack \
  --book-dir little-weather/standalone/nell-and-the-pocket-sized-storm \
  --audio little-weather/standalone/nell-and-the-pocket-sized-storm/exports/narration-v1 \
  --book-id nell-and-the-pocket-sized-storm
python3 tools/narration.py validate
python3 tools/build_catalog.py build
```

`tools/build_catalog.py` copies `narration/` into the build and adds a
`narration` block to that book's `catalog.json` entry. The reader shows a
**Listen** control only for fixed-layout books that have that block. It starts
only on a click, follows the current page, preloads only the next page, turns the
page when a track ends, and stops with a readable message if audio is missing or
blocked. Reflowable books do not get page audio without a separate chapter-level
contract.

Keep the layer honest:

- Only ship audio whose rights are recorded. Do not imitate an identifiable
  person without documented consent; a public dataset clip is not consent.
  Label synthetic stand-in voices as synthetic.
- `narration/` is not a place for drafts. Publish only takes that passed a
  per-page transcript and pause check and, for anything presented as finished,
  a human listen.
- EPUB and PDF remain silent reading editions. Do not add audio dependencies,
  media overlays or tags to them unless the author asks for a separate edition.
- The build scans every published EPUB's XHTML, and the PDF text when
  `pdftotext` is available, for tag tokens and fails on a hit.

## Audiobooks

A reflowable novel may ship chapter audio without using the fixed-layout page
narration package. *The Ledger of Ashes* uses:

| Path | Role |
| --- | --- |
| `site/audiobook.html` | Standalone chapter player, generated by the book's `production/build_audiobook_page.py` |
| `site/audio/the-ledger-of-ashes/chapters.json` | Chapter titles, durations, sizes and sha256 hashes |
| `site/audio/the-ledger-of-ashes/chapter-NN.mp3` | Mono 96 kbps chapter audio |

The page uses native `<audio controls preload="none">` elements. It never
autoplays. The site build copies `site/audio/` with the rest of `site/` and its
link checker verifies every audio URL. `tests/test_catalog.py` checks the 22
players, their files and hashes.

The current Ledger audio was rendered with Fish Audio Drama 3 from the 484
word-exact segments, in 25-page chunks at `max_tokens=1400`; pages that hit the
token cap were split at sentence boundaries. Coverage and hashes were checked,
with an 11-segment ASR spot check. **No human listening review has been
performed.** Do not describe it as an auditioned or finished performance. Keep
the render record and tagged script in the book's `production/narration/`; audio
never enters the EPUB or PDF.

## Local preview and checks

```sh
# Run the automated checks (manifest, hashes, EPUB packages, vendored libs)
python3 -m unittest discover -s tests -v

# Build the site into _site/
python3 tools/build_catalog.py build

# Preview exactly what will be deployed (the reader needs http, not file://)
python3 -m http.server 8000 --directory _site
# then open http://localhost:8000/
```

`python3 tools/build_catalog.py validate` runs the same validations without
writing output.

## What the checks verify

* Every manifest entry has a valid unique slug id, and the initial release
  set is present. The checks are metadata-driven: they validate the manifest
  against the actual files and built output, so adding an edition does not
  require test edits.
* Every selected file exists in `publications/`, matches its recorded size
  and sha256, and is a real package: PDFs have a `%PDF-` header and EOF
  marker; EPUBs open as zip archives with the uncompressed `mimetype` entry
  first, a parseable package document, a non-empty spine, and matching
  `dc:language` and `rendition:layout` values. A book labeled "fixed" or
  "reflowable" is checked against what the EPUB actually declares, so the
  catalog cannot mislabel a format.
* The vendored EPUB.js and JSZip files match the pinned sha256 checksums
  recorded in `site/assets/vendor/PROVENANCE.md`, and JSZip is loaded before
  EPUB.js in `reader.html`.
* The built output contains only relative URLs: absolute paths (which break
  under the `/books/` project path) and remote URLs fail the build.
* Every published artifact and cover is linked from a page, every book has a
  "Read online" link, and every `reader.html?book=<id>` link names a book the
  manifest actually lists, so nothing can be silently stranded or dangle.
* The build only ever deletes an output directory it owns: an empty
  directory, one marked `.generated-by-build_catalog` by a previous build,
  or a legacy `_site/` from earlier builds. The source root, its ancestors,
  symlinks and unrelated populated directories are refused before any
  cleanup; sentinel tests cover each case.
* When narration exists, every page file exists, matches its recorded size and
  sha256, pages are contiguous, the durations add up, the reader manifest agrees
  with the index, and the book is fixed-layout. The catalog entry carries the
  narration manifest URL, and the build copies `narration/` into `_site/`.
* No performance tag (`<|speaker:`, delivery spans, structural tokens) appears in
  a manuscript, the export Markdown, the published EPUB XHTML or, when
  `pdftotext` runs, the published PDF text.
* Studio and process files (manifest source paths, handoffs, and so on) are
  not copied into the site; `_site/` contains only `site/`, the selected
  `publications/` files, `narration/`, and `catalog.json`.

Known limit: the automated checks validate packages and output structure,
not the visual reading experience. Open the built site in a browser after any
reader or style change; the browser reader itself is not exercised by CI.

## Deploying

The workflow `.github/workflows/pages.yml` runs on pushes to `main` that change
the site, publication files, build tool, tests, or workflow itself. It can also
be started manually through Actions. It
runs the checks, builds `_site/`, uploads it with
`actions/upload-pages-artifact@v4`, and deploys it with
`actions/deploy-pages@v4` into the `github-pages` environment.

Pages must be enabled once, with Source set to "GitHub Actions", in the
repository settings. The site then serves at
`https://JorgeGarciaIrazabal.github.io/books/`. All URLs in the site are
relative, so the project subpath needs no configuration.

## Adding or updating an edition

1. Copy the finished export files, byte for byte, into `publications/`:

   ```sh
   cp <universe>/<series>/<book>/exports/<book>.epub  publications/
   cp <universe>/<series>/<book>/exports/<book>.pdf   publications/
   ```

   Do not rebuild or modify books for the website; publish the completed
   edition as reviewed. Existing exports are gitignored, which is why the
   tracked copies in `publications/` are the ones CI uses.

2. Record the file fingerprints for the manifest:

   ```sh
   python3 tools/build_catalog.py hash publications/<book>.epub
   python3 tools/build_catalog.py hash publications/<book>.pdf
   ```

3. Derive a cover from the published edition (do not create new artwork for
   the site). If the EPUB contains a cover image:

   ```sh
   python3 tools/build_catalog.py cover publications/<book>.epub --id <book>
   python3 tools/build_catalog.py hash publications/covers/<book>.jpg
   ```

   For an EPUB without images, render a page of the actual PDF instead, for
   example `pdftoppm -png -r 110 -f 1 -l 1 publications/<book>.pdf /tmp/cover`
   and convert to a 720-pixel-wide JPEG. Note the derivation honestly in the
   manifest's `cover.derived_from` field.

4. Add or update the book entry in `publications/manifest.json`: `id`, `title`,
   `summary` (grounded in the book's `brief.md`), `language` and `layout`
   exactly as the EPUB declares them, `downloads` with paths, bytes and
   sha256, the `cover` entry with its own hash, and `sources` pointing at the
   studio export paths for provenance. The manifest stays in the repository;
   only the public fields are projected into `_site/catalog.json`.

5. Add a static card to `site/index.html` (cover link, badges, summary,
   download buttons, and the `reader.html?book=<id>` link). The build fails
   if a published file is not surfaced, and if the card links a book the
   manifest does not list, the link check fails.

6. Run the checks and preview locally. When the author has authorized this
   release, share only its reviewed files on `main` using the
   [workspace sync guide](workspace-sync.md). Check the live edition before
   giving readers the link.

To replace an edition's files, copy the new files over the old ones and
update the manifest hashes and sizes in the same commit; the build fails on
any mismatch, which is intended protection against drift.

## Vendored reader libraries

The browser reader uses EPUB.js 0.3.93 (FreeBSD license) with JSZip 3.10.1
(MIT or GPLv3), vendored in `site/assets/vendor/` with their license texts
and pinned checksums in `site/assets/vendor/PROVENANCE.md`. The checksum test
fails if either file changes, so upgrading a library means updating the file,
its checksum in PROVENANCE.md, and reviewing the reader against the new
version together.

## Reader behavior notes

* The reader only opens books listed in `catalog.json`; it never loads an
  EPUB from an arbitrary external URL.
* Fixed-layout books (like Nell) offer two views. **Text** reflows the book's
  own page documents and illustrations into a continuous scroll on small
  screens (the default there), with text size controls and saved
  section/scroll. **Pages** fits the illustrated page to its native
  proportions. Reflowable books (like the Mila editions) paginate, offer text
  size controls, and are capped at a `46rem` measure.
* Wide desktop screens show a persistent contents rail; smaller screens use a
  slide-over drawer with an explicit close button. "Start over" lives in the
  contents panel so the reading header stays compact.
* Reading positions and text size are stored per book in the visitor's
  localStorage. If storage is unavailable (private mode and similar), the
  reader says so and works without saving.
* The Nell EPUB is a large illustrated fixed-layout file (about 29 MB), so
  the first open can take a moment on slow connections.
