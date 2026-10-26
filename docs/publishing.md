# Publishing to GitHub Pages

This guide covers how the public library site at
`https://JorgeGarciaIrazabal.github.io/books/` is assembled, checked, and
deployed, and how to add or update an edition.

## What lives where

| Path | Role |
| --- | --- |
| `site/` | Website sources: `index.html` (catalog), `reader.html` (browser EPUB reader), styles, scripts, icon, and the vendored reader libraries in `site/assets/vendor/`. |
| `publications/` | The tracked publication artifacts (`.epub`, `.pdf`), the derived cover images in `publications/covers/`, and `manifest.json` with byte sizes, sha256 hashes, and studio source paths for every file. |
| `tools/build_catalog.py` | Build tool: validates the manifest and the actual artifact packages, assembles `_site/` from `site/` and `publications/` only, and checks every URL in the output. |
| `tests/test_catalog.py` | Automated checks for manifest and artifact integrity, EPUB package behavior, vendored library pinning, and subpath-safe output. |
| `.github/workflows/pages.yml` | GitHub Pages deployment workflow. |
| `_site/` | Generated output (gitignored). Never edit or commit it; rebuild instead. |

The website is deliberately a static, buildless front end: no server, no
runtime CDN, no downloaded fonts. The only generated file is `catalog.json`,
written by the build tool from `publications/manifest.json`.

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
* Studio and process files (manifest source paths, handoffs, and so on) are
  not copied into the site; `_site/` contains only `site/`, the selected
  `publications/` files, and `catalog.json`.

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

6. Run the checks and preview locally, then commit and push to `main`.

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
* Fixed-layout books (like Nell) render one page at a time; reflowable books
  (like the Mila editions) paginate and offer text size controls.
* Reading positions and text size are stored per book in the visitor's
  localStorage. If storage is unavailable (private mode and similar), the
  reader says so and works without saving.
* The Nell EPUB is a large illustrated fixed-layout file (about 29 MB), so
  the first open can take a moment on slow connections.
