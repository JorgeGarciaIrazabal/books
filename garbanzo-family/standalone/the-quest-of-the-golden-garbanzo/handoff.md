# Handoff — The Quest of the Golden Garbanzo

## Current objective
Publicly released *The Quest of the Golden Garbanzo* (`stage: "released"`, `garbanzo-family` canon revision 3) to `publications/`, `site/`, and GitHub (`origin/main`), including reflowable EPUB 3, 32-page reading PDF, 720×1080 cover JPEG, and a 10-chapter synthetic audiobook.

## Completed and changed paths
- **Universe (`garbanzo-family/`, canon revision 3)**:
  - `garbanzo-family/universe.json`, `bible.md`, `glossary.md`, `canon.json` (`FACT-0001`..`FACT-0019`), `timeline.json` (`EVT-0001`..`EVT-0008`), `decisions.md` (`DEC-GF-0001`..`DEC-GF-0007`).
  - `garbanzo-family/characters/CHAR-0001-jorge.md`, `CHAR-0002-marissa.md`, `CHAR-0003-clara.md`, `CHAR-0004-garbanzo.md`, `CHAR-0005-poki.md`.
  - `garbanzo-family/standalone/series.json`, `bible.md`, `roadmap.md`.
- **Book (`garbanzo-family/standalone/the-quest-of-the-golden-garbanzo/`)**:
  - Planning & ledgers: `book.json` (`stage: "released"`, 32 PDF pages / 30 story pages), `brief.md`, `style.md`, `outline.md`, `scenes.json`, `knowledge.json`, `threads.json`, `decisions.md` (`DEC-QGG-0001`..`DEC-QGG-0004`), `state.md`, `tasks.json`, `production/brief.md`, `canon/proposals.json`.
  - Manuscript: `manuscript/001-the-kettle-that-refused-to-boil.md` through `manuscript/010-the-kingdom-of-free-mornings.md` (`8,474` words).
  - Production scripts & logs: `production/build_edition.py`, `production/build_audiobook.py`, `production/narration/render.json`.
  - Reviews & gates: `reviews/whole-book-dev-review.md`, `reviews/whole-book-canon-audit.md`, `reviews/issues.json`, `reviews/gates.json` (`GATE-0001`–`GATE-0007`).
- **Public release (`publications/` & `site/`)**:
  - `publications/manifest.json` (added `the-quest-of-the-golden-garbanzo`).
  - `publications/the-quest-of-the-golden-garbanzo.epub` (`84,694` bytes, sha256 `271eff75ac8b7e5500c465ee029f372e00e3d62703f65d907d913cf0d46dc5a1`).
  - `publications/the-quest-of-the-golden-garbanzo.pdf` (`195,478` bytes, 32 pages, sha256 `88f97ebf9c13e8c12fb37574572920d5a270382967b3c8d804b36a143e546f7e`).
  - `publications/covers/the-quest-of-the-golden-garbanzo.jpg` (`69,647` bytes, 720×1080 JPEG, sha256 `e9cb6e670dda97cb3a0fdc2566782cebd669069feacfc95cb2fb479c348828fc`).
  - `site/index.html` (`5 books`, catalog card with Read online, Listen to the audiobook, EPUB, and PDF links).
  - `site/audiobook-the-quest-of-the-golden-garbanzo.html` and `site/audio/the-quest-of-the-golden-garbanzo/{chapters.json,chapter-01..10.mp3}` (`54:24`, `39,178,520` bytes, Kokoro-82M ONNX `af_heart`).

## Accepted decisions / source snapshot
- `DEC-GF-0006` / `DEC-QGG-0003`: Confirmed wife's name as **Marissa**.
- `DEC-GF-0007` / `DEC-QGG-0004`: Authorized public release and push to GitHub Pages with EPUB, PDF, cover, and synthetic audiobook.
- Exact source and release artifact SHA-256 hashes recorded in `reviews/gates.json` (`GATE-0007`), `publications/manifest.json`, and `site/audio/the-quest-of-the-golden-garbanzo/chapters.json`.

## Open issues and assumptions
- Synthetic narration (`Kokoro-82M ONNX`, `af_heart`) passed file coverage, duration, byte size, and SHA-256 checks; **no human listening review** has been performed yet (especially checking pronunciation of Spanish phrases such as *cocido madrileño*, *entrega de llaves*, and *Valladolid*).
- Edge TTS (`en-US-AvaMultilingualNeural`) timed out twice during earlier synthesis attempts and was cleanly replaced with local Kokoro-82M ONNX across all 10 tracks for uniform voice.

## Next concrete action
- Open the live catalog at `https://JorgeGarciaIrazabal.github.io/books/` after GitHub Pages deploys, and spot-listen to Chapter 1 and Chapter 10 on `audiobook-the-quest-of-the-golden-garbanzo.html` to verify pronunciation of Spanish terms and family names.
