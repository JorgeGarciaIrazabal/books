# Handoff — The Hot Potato of Corporate Castle

- **Date**: 2026-11-26
- **Role**: `studio_director`
- **Canon revision**: `3` (`corporate-castle/universe.json`; includes `DEC-CC-0007` honoring Liability's branch of Deep Magic and contrasting Lois's personal failure with Sir Leo).

## Completed work
- Built, visually proofed, and published the **Prologue Preview Edition** (strictly `manuscript/000-prologue-the-hot-potato-of-corporate-castle.md`, excluding draft Chapter 1):
  - Created `production/build_edition.py` generating a 720×1080 typographic cover, a 4-page 6×9 reading PDF, and a reflowable EPUB 3 with word-exact prose verification.
  - Visually inspected rendered cover and PDF pages (tightened body leading/margins to eliminate a two-line Page 5 widow; centered the `PROLOGUE PREVIEW` badge and title spacing).
  - Copied verified exports to `publications/the-hot-potato-of-corporate-castle.{epub,pdf}` and `publications/covers/the-hot-potato-of-corporate-castle.jpg`.
  - Registered the edition in `publications/manifest.json` and added its catalog card to `site/index.html` (`6 books`).
  - Rebuilt `_site/` via `tools/build_catalog.py build` and ran `tests/test_catalog.py` + `tools/studio.py check`.
- Updated `manuscript/001-the-reluctant-steward.md` (still draft/unpublished) with live on-page Squire Deep Magic moments for Victoria and Riley and `DEC-CC-0007` Liability respect.

## Remaining open items
- Confirm whether the author wants to commit and push to GitHub Pages (`origin/main`) now (and whether to push only Corporate Castle or also include existing uncommitted local edits such as the Golden Garbanzo illustrated update).
- Author feedback on draft Chapter 1 (`manuscript/001-the-reluctant-steward.md`) before drafting Chapter 2 (*The Fracture*).
- Final title selection and later reexamination of Tab 3 back-half drafts (Chapters 5+).

## Next concrete action
Await author go-ahead to commit/push the Prologue Preview to GitHub Pages, or continue refining Chapter 1 and drafting Chapter 2.
