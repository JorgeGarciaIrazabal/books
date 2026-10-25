# EPUB export verification — 2026-10-25

Scope: the existing complete manuscript exported for Android phones and tablets, with no prose changes. Director performed production work directly; this is not a fresh independent editorial review.

Source snapshot: the twelve chapter SHA-256 hashes in `exports/epub-manifest.json`, compared with the existing PDF build manifest and final full-reader report. Existing reader coverage remains applicable to unchanged source text. EPUB output SHA-256 is in the EPUB manifest; builder SHA-256 is recorded there as well.

Actual checks on `exports/mila-and-the-missing-moon.epub`:

- ZIP integrity, correct first uncompressed mimetype entry, and XML parsing passed.
- All twelve chapters follow `book.json` order. Every chapter's paragraphs were extracted from the archived XHTML and compared with the source, preserving text and emphasis content; all passed.
- The navigation document links to title, all twelve chapters, and the optional questions in order. All local links resolve. PDF page-break markers are absent.
- EPUBCheck 5.4.0 returned zero fatal messages, errors, warnings or informational findings. Exact output is recorded in `exports/epubcheck.json`.
- Reflowable layout uses relative sizes and no fixed page dimensions, body text color or background. No forced PDF page breaks remain.

Limitations: no physical Android device, Google Play Books account import or reading-app visual proof was performed. EPUBCheck assesses format conformance, not device behavior or literary quality. The EPUB title is typographic with a decorative moon and star; PDF drawings are omitted. EPUB pages vary by screen and user settings. Existing PDF and manuscript remain unchanged.
