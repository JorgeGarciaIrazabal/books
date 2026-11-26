# Handoff — The Hot Potato of Corporate Castle

- **Date**: 2026-11-26
- **Role**: `studio_director`
- **Canon revision**: `3` (`corporate-castle/universe.json`).

## Completed work
- Published **Prologue Preview Edition** (EPUB 3, 4-page PDF, 720×1080 cover) live to GitHub Pages (`91712e2`).
- Rendered, ASR-checked, retaken, assembled, and published **Prologue Preview Audiobook** (strictly Prologue only, excluding draft Chapter 1):
  - Engine: local **Fish Audio Drama 3** (`audio.cpp` Vulkan, synthetic `af_heart` narrator reference).
  - 11 word-exact segments (`production/narration/segments.json`, `script.md`, `cast.json`, `cast/narrator.wav`, `render.json`, `notes.md`).
  - Faster-whisper ASR check caught two stumbles (`u02` *"full-blown"*, `u10` *"Volun-telling"*) — retaken cleanly at seed 11 -> final check: **0 flagged, 0 word errors, 0.0s runaway pauses, mean 155.6 wpm**.
  - Assembled `site/audio/the-hot-potato-of-corporate-castle/chapter-01.mp3` (`5:05`, `3,659,660` bytes) + `chapters.json`, created `site/audiobook-the-hot-potato-of-corporate-castle.html`, and linked from `site/index.html`.
  - Validated EPUB/PDF tag exclusion (`tools/narration.py validate`), rebuilt `_site/`, passed all 60 unit tests, and pushed live to `origin/main`.

## Remaining open items
- Human listening review of the synthetic Prologue audio (mechanical ASR/pause checks pass; warmth/pronunciation of proper nouns like `Sarai` and `Okta` still benefit from human ear).
- Author feedback on draft Chapter 1 (`manuscript/001-the-reluctant-steward.md`) before drafting Chapter 2 (*The Fracture*).
- Final title selection and later reexamination of Tab 3 back-half drafts (Chapters 5+).

## Next concrete action
Review draft Chapter 1 with the author, incorporate any notes, and draft **Chapter 2: The Fracture** (or retake any Prologue audio segment if human listening catches a pronunciation tweak).
