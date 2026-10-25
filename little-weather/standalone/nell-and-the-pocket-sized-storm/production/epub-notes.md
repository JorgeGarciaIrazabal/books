# EPUB edition

User approved the redesigned appearance and requested EPUB. The fixed-layout EPUB3 preserves all30storypages, sixchapters and twelveillustrations from illustrated-v3, with selectable XHTML text, the same16.8pt type, original PNG artwork/alpha, three embedded Noto font files, descriptive image alternatives, six chapter links and30page targets. The library thumbnail is a render of the existing first page; it adds no spine page. No author or publisher credit was invented.

File: exports/nell-and-the-pocket-sized-storm.epub
SHA256: 5027cc6302965743f55ed9c8e5f69087b0a72ec961093112426002752eb0fa7e
Size: 30,826,128 bytes

## Build and verify

```sh
python3 little-weather/standalone/nell-and-the-pocket-sized-storm/production/build_epub.py
java -jar /tmp/mila-epubcheck/epubcheck-5.4.0/epubcheck.jar little-weather/standalone/nell-and-the-pocket-sized-storm/exports/nell-and-the-pocket-sized-storm.epub --json little-weather/standalone/nell-and-the-pocket-sized-storm/reviews/epub/epubcheck.json
python3 little-weather/standalone/nell-and-the-pocket-sized-storm/production/verify_epub.py
```

Builder uses Python standard library, local installed Noto fonts/copyright notice and Poppler pdftoppm for the library thumbnail. Proof additionally needs Node and Chrome/Chromium; EPUBCheck needs Java. EPUBCheck was already available locally at the path above; it was not downloaded for this task. Preserve/read the recorded modified timestamp in exports/epub-manifest.json for deterministic rebuilds. Expanded deliverable files are in exports/epub/. The distributed EPUB itself embeds all reading resources and fonts. Font copyright/OFL notice is included in the archive.

## Evidence
EPUBCheck5.4.0 passed with zero errors, warnings or fatal messages. Initial navigation aria-label attributes failed this version's schema and were removed; headings still name the navigation sections. After the correction, validation passed.

Actual ZIP bytes were extracted to a new temporary directory and each of30XHTMLdocuments loaded directly in Chrome using the DevTools Protocol. The proof awaited document load, document.fonts.ready and decoded images. All paragraphs, headings, picture positions and folios match the approved HTML within0.15CSSpx, with no differences found. Text is actual selectable XHTML; all293proseparagraphs match the manuscript, including page order. Links/fragments and local resources resolve. The independent reviewer inspected the actual archive, all12picturepages and5additionalchapteropenings. Other13pages had full text/geometry checks, without independent visual inspection. Screenshots/hash bindings are in reviews/epub/.

The PDF, original artwork, manuscript and page-design inputs remain unchanged. This is a browser-rendered proof of EPUB resources, not an installed Apple Books/Kindle/device test or accessibility certification. Fixed page designs require page scaling/zoom rather than reflowed font resizing. No publication or external book upload occurred.

## Primary specification references
- [W3C EPUB fixed layout](https://www.w3.org/TR/epub-33/#sec-fixed-layouts): pre-paginated rendition, viewport metadata and spread control.
- [W3C EPUBCheck](https://www.w3.org/publishing/epubcheck/): conformance checker used on the actual EPUB archive.

No universal reading-app compatibility claim is inferred from standards validation.
