# Illustrated-v3 reading edition

30 story pages at 7.5 × 9.5 inches, title on page1, six chapters, twelve pictures, two per chapter. Body16.8pt; leading/paragraph spacing are page-specific in layout-v3.json. Original story prose remains unchanged.

The author rejected illustrated-v2's repeated small inset images. That edition is archived in production/previous-edition/illustrated-v2/. V3 uses six transparent vignettes, three uncropped full-width scene paintings and three portrait paintings with quiet sky reserved for text. No running headers or rules; discreet outside folios. Two-column prose on pages9/17 preserves readable type with large art. All other pages have explicit compositions.

Selected art and alt text: illustration-plan.json. Placement geometry: layout-v3.json. New prompts and local repairs: prompts/redesign/. Source/reference/output provenance: redesign-generation-run.json. Original PNG dimensions and alpha retained. Full-width retained paintings are uncropped. Near-page-ratio portrait backgrounds have a deliberate minimal horizontal crop, with actual fraction recorded by the build.

Rebuild from repository root:

```sh
python3 little-weather/standalone/nell-and-the-pocket-sized-storm/production/build.py
python3 little-weather/standalone/nell-and-the-pocket-sized-storm/production/verify_illustrated.py
```

Requires Python3, Pillow, local Chrome/Chromium, and Poppler pdfinfo/pdftotext/pdfimages. No imagegeneration/network required to rebuild. Self-contained HTML and PDF are generated under exports/. Source/output hashes, actual placed dimensions/PPI, alpha and crop data are in exports/reading-edition-manifest.json. Browser geometry measures all actual paragraphs and images. Mechanical fidelity/geometry checks and independent aesthetic review are distinct.

This is a private digital reading edition. Meaningful image alternatives are present in HTML; PDF accessibility has not been certified. No publication, physical print proof or rights clearance is represented. Generated art used the built-in image tool; the underlying image model was not exposed. Final aesthetic acceptance remains with the author.


## EPUB companion
The author approved the redesigned appearance and requested an EPUB. exports/nell-and-the-pocket-sized-storm.epub preserves the30page designs as a fixed-layout EPUB3 with selectable text, embedded Noto fonts, chapter/page navigation and12original illustrations. See epub-notes.md for build/validation commands and limits. Exact EPUB inputs/archive hash are in exports/epub-manifest.json; actual package/conformance/page proofs in reviews/epub/. PDF inputs and exports are unchanged.
