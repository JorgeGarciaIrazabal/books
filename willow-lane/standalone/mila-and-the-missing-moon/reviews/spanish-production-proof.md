# Spanish reading edition — production proof

2026-10-25. Production performed directly by studio_director. Actual export checks, separate from the fresh native copy_editor's bilingual text review. No independent device/physical proof performed.

Sources: `production/spanish-runtime/final-text-snapshot.json` identifies all thirteen final Spanish source files. All source hashes match the built EPUB manifest and the PDF chapter manifest. The initial bilingual review read all twelve English/Spanish chapter pairs; the repair recheck read all twelve final Spanish chapters and the question page, plus relevant English passages, and resolved every required finding. The optional chapter-four “por él” reference clarification remains optional, with current text preserved.

Actual deliverables: twelve chapters, 7,742 story words; fifty-page 7 × 10 inch PDF with original vector drawings; reflowable Spanish EPUB with linked contents and correct `es` language metadata; editable Markdown with complete translated prose. The shared questions are included in all formats. No author byline or reception claim was invented.

Checks performed:
- PDF build used fixed 13.2-point type / 18.4-point leading and passed explicit bottom-bound checks. Exactly fifty pages: one title, forty-eight story, one shared-question page.
- Extracted all forty-eight story pages from the actual PDF and checked each complete corresponding source unit, correct dimensions and absence of printed layout comments. Checked final question-page heading and all question text. All passed.
- Actual EPUB ZIP integrity, XML parsing, spine order, all local links, every chapter paragraph, afterword text and document language tags passed. EPUBCheck 5.4.0 returned zero fatal messages, errors, warnings or infos; see `exports/epubcheck-es.json`.
- Director visually inspected rendered final PDF pages 1, 2, 34, 42, 49 and 50, including cover, chapter/solution text, ending and questions. No clipped text or overflow found on these pages. Renders are temporary under `/tmp/mila-spanish-proof/`.
- All English source SHA-256 hashes remain equal to the original input snapshot; original English PDF and EPUB bytes are preserved. Updated EPUB builder was also exercised against the English edition in a temporary output directory and produced a byte-identical EPUB.

Exact output SHA-256 inventory:

```text
4ffed331d853ee52794e3c2e38b0b2ebe0ada6eeb466792cb0042a0c340e0452  exports/mila-y-la-luna-perdida.epub
18f8eaa86c49281003fc5e19d8ef6b63cba8ca5341d3ff7e251493dc495c248b  exports/mila-y-la-luna-perdida.pdf
52b0a1c6b3bc3db9b541b316849a939d40754db40e97e5b86905d8e0c5c517a6  exports/mila-y-la-luna-perdida.md
```

Limitations: no physical Android device, Google Play Books import, human Spanish proofreader, child/parent read-aloud or print proof was tested. Mechanical validation is not literary or publication certification. EPUB illustrations are the text ornament only; the PDF retains vector art. No commit, upload or publication performed. Complete delivery and source metadata: `exports/spanish-delivery.json`.

The final studio structure helper returned zero structural errors and noted thirteen manuscript files excluded from the English root chapter order. These are the twelve Spanish chapters and supplementary page, intentionally ordered separately in editions/es.json; both Spanish builders checked the chapter correspondence against book.json.
