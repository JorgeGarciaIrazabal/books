# Decision history — The Quest of the Golden Garbanzo

## DEC-QGG-0001: Ten-chapter 30-page structure and text-only first edition
- **Date**: 2026-11-22
- **Question**: How should the requested 30-page fantasy book be paced and formatted?
- **Accepted choice**: Ten chapters at roughly 780 to 830 words each (total ~7,800 to 8,300 words, corresponding to ~30 pages at ~265 words/page in 5.5 x 8.5 in keepsake formatting), produced as a text-first reading edition with Markdown, HTML, and EPUB 3 exports.
- **Rationale**: Allows rich dramatic buildup, comic set pieces, and read-aloud pacing suitable for Clara alongside grown-up wit for Jorge and Marisa.
- **Authority**: Delegated studio_director design within user request ("create a small book (30 pages)").
- **Affected paths**: `brief.md`, `outline.md`, `book.json`.

## DEC-QGG-0002: Reversible standardization on Marisa
- **Date**: 2026-11-22
- **Question**: Use `Marisa` or `Marissa` in Book 1?
- **Accepted choice**: Use `Marisa` per `DEC-GF-0001`; preserve `Marissa` note in handoff so the author can flip spelling in one pass if desired.
- **Affected paths**: `brief.md`, `manuscript/*.md`.

## DEC-QGG-0003: Author confirmation of Marissa (supersedes DEC-QGG-0002)
- **Date**: 2026-11-22
- **Question**: Author confirmed wife's name is **Marissa**.
- **Accepted choice**: Replace `Marisa` with **Marissa** across Book 1 planning files, all 10 manuscript chapters, and rebuilt Markdown/HTML/EPUB exports (`DEC-GF-0006`). Historical blind review reports (`reviews/whole-book-*.md`) and `DEC-QGG-0001`/`DEC-QGG-0002` text remain preserved as historical records.
- **Authority**: Explicit author instruction (`2026-11-22`).
- **Supersedes**: `DEC-QGG-0002`.
- **Affected paths**: `brief.md`, `style.md`, `outline.md`, `scenes.json`, `knowledge.json`, `state.md`, `production/brief.md`, `canon/proposals.json`, `manuscript/001..010*.md`, `exports/*`, `handoff.md`, `reviews/gates.json`.

## DEC-QGG-0004: Public GitHub Pages release with EPUB, PDF, cover, and audiobook
- **Date**: 2026-11-23
- **Question**: Release Book 1 publicly with chapter audio per author request?
- **Accepted choice**: Build publication EPUB 3, 32-page PDF, 720×1080 cover JPEG, and 10-chapter synthetic audiobook (`Kokoro-82M ONNX`, voice `af_heart`), stage in `publications/` and `site/`, set `stage: "released"`, and push release files to `origin/main`.
- **Authority**: Explicit author instruction (`2026-11-23`; `DEC-GF-0007`).
- **Affected paths**: `book.json`, `production/*`, `publications/*`, `site/*`, `reviews/gates.json`, `handoff.md`.

## DEC-QGG-0005: Full rewrite as grounded human, easy-reading edition
- **Date**: 2026-11-23
- **Question**: Author asked to make the story less magical (family remain humans), lower the reading level so it is easy to read and understand (less dense), while staying fun and dramatic, via a full rewrite of the whole book.
- **Accepted choice**: Rewrite all 10 chapters from scratch in plain, crisp Grade 5–6 English (~7,000–7,600 words targeting ~30 story pages), keeping the family completely human with only three warm light-magic touches (Golden Garbanzo pot, Garbanzo the mini desk-bot, Poki's gentle silver visits), rebuilding PDF/EPUB/cover/audiobook locally without pushing to Git until user review.
- **Authority**: Explicit author instruction (`2026-11-23`; `DEC-GF-0008`).
- **Affected paths**: `brief.md`, `style.md`, `outline.md`, `scenes.json`, `knowledge.json`, `threads.json`, `book.json`, `manuscript/*.md`, `production/*`, `reviews/*`, `publications/*`, `site/*`, `handoff.md`.
