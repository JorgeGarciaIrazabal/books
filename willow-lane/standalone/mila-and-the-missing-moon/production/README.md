# Build the reading edition

The ordered source chapters are declared in `../book.json`. Each contains four designed page units separated by `<!-- PAGEBREAK -->`. Edit the source chapters, then rebuild; exports are generated files.

From the library root, using a Python environment with `production/requirements.txt` installed:

```sh
python willow-lane/standalone/mila-and-the-missing-moon/production/build.py
python willow-lane/standalone/mila-and-the-missing-moon/production/verify.py
python tools/studio.py check willow-lane/standalone/mila-and-the-missing-moon
```

The build uses DejaVu Serif and DejaVu Sans from `/usr/share/fonts/truetype/dejavu/`. It produces a 7 × 10 inch PDF with fifty pages, an editable assembled Markdown file, and a source hash inventory. The first page is the title; pages 2–49 contain the story; page 50 holds optional shared questions. The PDF includes chapter bookmarks. Body type is 13.2 points with 18.4-point line spacing. Artwork consists of original vector shapes drawn by the build script.

The build rejects text that would cross the lower page boundary. The verifier checks all forty-eight story pages against the source text extracted from the actual PDF. These are mechanical completeness checks; independent reading reports live in `../reviews/`.

## EPUB for Android phones and tablets

Using Python 3 (standard library only):

```sh
python3 willow-lane/standalone/mila-and-the-missing-moon/production/build_epub.py
```

This builds `exports/mila-and-the-missing-moon.epub` directly from the chapter order in `book.json`, plus `exports/epub-manifest.json`. It removes PDF pagination markers while preserving paragraphs and emphasis, provides a linked contents page, and includes the same optional shared questions. It does not impose a fixed font size, page size, text color or background color. No author name is invented. The text-only title page uses a decorative moon and star; PDF illustrations are not included. EPUB page count depends on the reader settings and screen.

The builder checks the actual ZIP container, XML parsing, chapter order, every chapter paragraph against its source, and all local navigation links. For standards validation, use [W3C EPUBCheck](https://github.com/w3c/epubcheck/releases); this edition was validated with version 5.4.0:

```sh
java -jar /path/to/epubcheck.jar willow-lane/standalone/mila-and-the-missing-moon/exports/mila-and-the-missing-moon.epub --json willow-lane/standalone/mila-and-the-missing-moon/exports/epubcheck.json
```

Re-run both after source changes. The ZIP timestamps and edition metadata timestamp are fixed for reproducible builds; update the latter when creating a new edition. Physical Android app rendering and account import have not been tested. EPUBCheck is a format validator, not a literary review.

## Spanish edition

`editions/es.json` specifies translated chapter paths corresponding exactly to the English order in `book.json`, localized metadata, and the translated question page. Spanish sources are under `manuscript/es/`; they are the source of truth for the Spanish exports. `production/spanish-brief.md` records language/audience choices. Native Mistral Large 4 invocation evidence is under `production/spanish-runtime/`.

```sh
python production/build.py --edition es
python3 production/build_epub.py --edition es
python production/verify.py --edition es
java -jar /path/to/epubcheck.jar exports/mila-y-la-luna-perdida.epub --json exports/epubcheck-es.json
```

Run these commands from this book directory, with the PDF Python dependencies installed. The PDF retains fifty pages and the original vector drawings; the EPUB flows with the display and reader settings. Outputs use `mila-y-la-luna-perdida` filenames and separate `*-es.json` verification manifests, preserving English exports. The editable Spanish Markdown contains the complete translated text. Rebuilding the EPUB after the PDF also assembles the same text in Markdown without forcing PDF page breaks.
