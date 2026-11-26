# Handoff — The Quest of the Golden Garbanzo

## Current objective
Published the illustrated edition of *The Quest of the Golden Garbanzo* (`stage: "released"`) to `origin/main` and GitHub Pages: 8 interior illustrations at the book's most pivotal moments plus a new illustrated cover, rebuilt 36-page 6 × 9 in PDF, reflowable EPUB 3, and 720 × 1080 cover JPEG with zero changes to manuscript prose.

## Completed and changed paths (2026-11-25 Illustrated edition retrofit)
- **Quota-efficient illustration assets (`assets/illustrations/`, 4 total image-generator calls)**:
  - `assets/illustrations/ref-cast.png` (1376 × 768 cast/prop reference sheet; duplicate Clara figure masked cleanly onto cream paper).
  - `assets/illustrations/sheet-01.png` & `assets/illustrations/sheet-02.png` (two 1264 × 848 2 × 2 grids, 1 generation call each referencing `ref-cast.png`), cropped cleanly into `ill-0001.png`–`ill-0008.png` (`625 × 417` / `626 × 418`, Ch 1, 3, 4, 5, 6, 7, 9, 10; tiny `"ZERO"` brochure text cleaned from `ill-0004.png`).
  - `assets/illustrations/cover-art.png` (848 × 1264 portrait cover artwork, 1 single call referencing `ref-cast.png`).
- **Design records & edition builder**:
  - `production/visual-style.md`, `production/illustration-plan.json` (hashes, pixel sizes, placement, disclosure boundaries, alt text, PDF page numbers), `production/brief.md`, `book.json` (`pages: 36`, `illustrated: true`, `interior_illustrations: 8`).
  - `production/build_edition.py` — updated with cross-platform Linux/Windows fonts, illustrated cover composition, JPEG-compressed framed PDF illustrations (`KeepTogether` with captions), and semantic `<figure class="story-art">` EPUB 3 embedding with strict prose-fidelity and alt-text verification.
- **Updated publication artifacts (`publications/` & `site/index.html`, published to `origin/main`)**:
  - `publications/the-quest-of-the-golden-garbanzo.epub` (`1,032,927` bytes, sha256 `09bb23c41e460b567cbbae35558bbc06b1c4dc5d9562c73d928b11fbc1cd9c0d`, 8 embedded illustrations + illustrated cover).
  - `publications/the-quest-of-the-golden-garbanzo.pdf` (`1,480,469` bytes, 36 pages, sha256 `e2e626dc64f16659fb85533c9ffbcf39e182dc83e77ae2b35444b6645658eb19`, cover on p. 1, interior illustrations on pp. 5, 12, 16, 19, 22, 25, 32, 36).
  - `publications/covers/the-quest-of-the-golden-garbanzo.jpg` (`279,321` bytes, 720 × 1080, sha256 `20745a5a9aa6642432cdc4e10057b65f4b56876c6e9af23bebc39ad3e46814f1`).
  - `publications/manifest.json` & `site/index.html` updated (file sizes, hashes, Illustrated badge, cover alt text).
- **Verification**:
  - Visual inspection covered `ref-cast.png`, `cover-art.png`, both 2 × 2 sheets, all 8 cropped interior panels (`ill-0001.png`–`ill-0008.png`), and all 9 picture-bearing PDF pages rendered at 110 dpi via `pdftoppm` (`p. 1` cover twice after typography spacing polish, plus `pp. 5, 12, 16, 19, 22, 25, 32, 36`). Verified consistent character identities, sleek costume-free Poki (`FACT-0010`), non-cooking Jorge (`FACT-0009`), disclosure timing (no unicorn sticker on Garbanzo in Ch 1/3, zero confetti in Ch 10), and zero layout collisions.
  - `validate_plan.py --check-assets`, `tools/narration.py validate`, `tools/build_catalog.py build` (`_site/`), and `python3 -m unittest discover -s tests -v` (60/60 tests) all passed.
  - Limit: visual proofing was done by the same coordinator session (no separate `illustration_reviewer` subagent session), and browser visual inspection of the EPUB reader was not run yet.

## Completed and changed paths (2026-11-23 Drama 3 audiobook update, published in `f1dd633`)
- **Narration layer (`garbanzo-family/standalone/the-quest-of-the-golden-garbanzo/production/`)**:
  - `production/build_audiobook.py` — updated to invoke `tools/drama3.py` (Fish Audio Drama 3) instead of Kokoro-82M ONNX.
  - `production/brief.md` — updated release checklist entry for Fish Audio Drama 3.
  - `production/narration/segments.json` & `production/narration/script.md` — 97 word-exact chapter segments (`<=95` words, `8,252` spoken words, never crossing chapter boundaries).
  - `production/narration/cast/narrator.wav` & `production/narration/cast.json` — 5.5 s synthetic American English narrator reference (`af_heart`, sha256 `75e8edd35b2f86d0309b3aa6925699603e1f562f0934194e9a949874688fdec2`) with full provenance and Fish Audio Community License v1.0 attribution rules.
  - `production/narration/render.json` & `production/narration/notes.md` — full Drama 3 engine, model hash (`05af716baf78e7c20863b9ccebb3ebdeca9607dd3ea7d0b72c35079e675b212b`), settings, retake notes, and per-chapter checksums.
  - Local gitignored working render & ASR report: `exports/narration-drama3/` (`page-01..97.wav`, `render-summary.json`, `checks.json`).
- **Site audio & player (`site/`, published to `origin/main`)**:
  - `site/audio/the-quest-of-the-golden-garbanzo/{chapters.json,chapter-01..10.mp3}` — 10 mono 24 kHz 96 kbps MP3s (`54:23` / `3,263.448` s, `39,164,696` bytes total, `"Built with Fish Audio"` attribution included).
  - `site/audiobook-the-quest-of-the-golden-garbanzo.html` — updated chapter durations, total runtime (`54:23`), and Drama 3 narration notice.
- **Verification**:
  - All 97 segments rendered in Drama 3 on Vulkan (`seed=7`, `0` capped segments) and checked with `faster-whisper` (`small.en`, `beam_size=5`) + `silencedetect`.
  - Retook 5 units (`u26, u35, u47, u80, u81`) at `seed=11` to eliminate silences/drops (`u26` 7.2 s → 2.4 s, `u35` 18.5 s + 14-word drop → 0.0 s with all words restored, `u47` 4.5 s → 0.0 s, `u80` restored `"waist"`, `u81` calmed pace). Only 1 mechanical flag remains (`u83`, `sim=0.889`, verified as ASR homophones/digits like `zipping`/`12`/`3`/`14`).
  - `tools/narration.py validate` (0 leaked tags across 5 EPUBs and 5 PDFs), `tools/build_catalog.py build` (5 books built into `_site/`), and `python3 -m unittest discover -s tests -v` (60/60 tests) all passed.

## Previous rewrite record (already published in `8d9cb24`)
- **Universe (`garbanzo-family/`, canon revision 4)**:
  - `garbanzo-family/universe.json`, `bible.md`, `glossary.md`, `canon.json` (`FACT-0001`..`FACT-0019`), `timeline.json` (`EVT-0001`..`EVT-0008`), `decisions.md` (`DEC-GF-0008`).
  - `garbanzo-family/characters/CHAR-0001-jorge.md` through `CHAR-0005-poki.md`.
  - `garbanzo-family/standalone/bible.md`, `roadmap.md`.
- **Book (`garbanzo-family/standalone/the-quest-of-the-golden-garbanzo/`)**:
  - `book.json` (`stage: "released"`, `8,255` words, `33` PDF pages / `31` story pages), rewritten 10-chapter manuscript (`manuscript/001-*.md`..`010-*.md`), and published EPUB/PDF/cover in `publications/` remain unchanged.

## Accepted decisions / assumptions
- `DEC-GF-0008` / `DEC-QGG-0005`: Ordinary-human rewrite in plain ~Grade 5–6 English with three light magical elements.
- Reversible narration assumption: single warm American synthetic narrator (`af_heart` reference rendered through Fish Audio Drama 3) with `[warm, lively storyteller voice]` direction, matching the book's American English setting and keeping pacing brisk (`~155 wpm`).

## Open issues and assumptions
- Same-model independence limit on `rewrite-dev-review.md` and `rewrite-canon-audit.md`.
- Drama 3 narration passed full 97-segment mechanical ASR, pause, duration, size, and SHA-256 checks; **no human listening review** has been performed yet (note `u35` ASR transcribed `"moving"` as `"everything"` — worth a quick spot-listen).

## Next concrete action
- Open the updated live audiobook at `https://JorgeGarciaIrazabal.github.io/books/audiobook-the-quest-of-the-golden-garbanzo.html` once GitHub Pages finishes building, and spot-listen to Chapter 1, Chapter 4 (segment 35), and Chapter 10.
