# Handoff — The Quest of the Golden Garbanzo

## Current objective
Republished the grounded-human, easy-reading rewrite of *The Quest of the Golden Garbanzo* (`stage: "released"`, `garbanzo-family` canon revision 4, `DEC-GF-0008`, `DEC-QGG-0005`) to `publications/`, `site/`, and GitHub (`origin/main`), including 33-page reading PDF (31 story pages), reflowable EPUB 3, 720×1080 cover JPEG, and 10-chapter synthetic audiobook.

## Completed and changed paths
- **Universe (`garbanzo-family/`, canon revision 4)**:
  - `garbanzo-family/universe.json`, `bible.md`, `glossary.md`, `canon.json` (`FACT-0001`..`FACT-0019`), `timeline.json` (`EVT-0001`..`EVT-0008`), `decisions.md` (`DEC-GF-0008`).
  - `garbanzo-family/characters/CHAR-0001-jorge.md` through `CHAR-0005-poki.md`.
  - `garbanzo-family/standalone/bible.md`, `roadmap.md`.
- **Book (`garbanzo-family/standalone/the-quest-of-the-golden-garbanzo/`)**:
  - Planning & ledgers: `book.json` (`stage: "released"`, `8,255` words, `33` PDF pages / `31` story pages), `brief.md`, `style.md`, `outline.md`, `scenes.json`, `knowledge.json`, `threads.json`, `decisions.md` (`DEC-QGG-0005`), `state.md`, `tasks.json` (`TASK-0006`), `production/brief.md`, `canon/proposals.json`.
  - Rewritten manuscript (10 fresh chapters, average `11.88` words/sentence, `0` em/en dashes or `--`):
    `manuscript/001-the-golden-chickpea-goes-cold.md` through `manuscript/010-tuesday-at-ten-oclock.md` (old fantasy-heavy chapter files removed).
  - Reviews & gates: `reviews/rewrite-dev-review.md`, `reviews/rewrite-canon-audit.md`, `reviews/issues.json`, `reviews/gates.json` (`GATE-0008`–`GATE-0010`).
  - Production scripts & local builds: `production/build_edition.py`, `production/build_audiobook.py`, `production/narration/render.json`, `exports/*`.
- **Local catalog & audio staging (`publications/` & `site/`, unstaged/unpushed)**:
  - `publications/manifest.json` updated.
  - `publications/the-quest-of-the-golden-garbanzo.epub` (`82,485` bytes, sha256 `10753a01c30d241d9d53d893cf965916378d0ca39953f88d26d68321d9d99fe4`).
  - `publications/the-quest-of-the-golden-garbanzo.pdf` (`194,873` bytes, 33 pages / 31 story pages, sha256 `27961e2b2435a48bf54939d12cc7c2f1bc6d5c9547a7e22f784d0ac16030d7cb`).
  - `publications/covers/the-quest-of-the-golden-garbanzo.jpg` (`68,694` bytes, 720×1080 JPEG, sha256 `3d9f2a07841d923122199fa96d5d394fbdb8e4af5d0786b5b8073ea450080b47`).
  - `site/index.html`, `site/audiobook-the-quest-of-the-golden-garbanzo.html`, and `site/audio/the-quest-of-the-golden-garbanzo/{chapters.json,chapter-01..10.mp3}` (`51:45` / `3,105.262` s, `37,273,976` bytes total, Kokoro-82M ONNX `af_heart`).

## Accepted decisions / assumptions
- `DEC-GF-0008` / `DEC-QGG-0005`: Rewrote story around ordinary human life in New Jersey, Manhattan, and Spain with three light magical elements (Golden Garbanzo pot, Garbanzo the desk-bot, Poki's silver starlight visits) in plain ~Grade 5–6 English, and republished to `origin/main` per author instruction (`"when you are done, publish"`).

## Open issues and assumptions
- Same-model independence limit on `rewrite-dev-review.md` and `rewrite-canon-audit.md` (ran in fresh Antigravity Gemini 4 Neon subagents while Codex quota was exhausted).
- Synthetic narration (`Kokoro-82M ONNX`, `af_heart`) passed file coverage, durations, sizes, and SHA-256 checksums; **no human listening review** has been performed yet.

## Next concrete action
- Open the updated live edition and 10-track audiobook at `https://JorgeGarciaIrazabal.github.io/books/` once GitHub Pages finishes building, and spot-listen to Chapter 1 and Chapter 10 to check pronunciation and family names.
