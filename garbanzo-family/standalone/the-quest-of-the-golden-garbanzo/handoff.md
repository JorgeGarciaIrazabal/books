# Handoff — The Quest of the Golden Garbanzo

## Current objective
Updated the 10-chapter audiobook for *The Quest of the Golden Garbanzo* (`stage: "released"`) from Kokoro-82M ONNX to **Fish Audio Drama 3** (local `audio.cpp` `04ce54d0d22b` on Vulkan via `tools/drama3.py`), keeping the manuscript, EPUB 3, PDF, and cover unchanged.

## Completed and changed paths (2026-11-23 Drama 3 audiobook update)
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
