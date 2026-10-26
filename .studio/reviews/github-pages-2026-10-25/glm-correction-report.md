# Native OpenCode GLM 5.3 Cloud correction report

Session: `ses_e8a89bc4effeG4LVKz77zDjoyL`. Model: `ollama/glm-5.3:cloud#low`. The following is the specialist's final report, preserved verbatim; coordinator verification is recorded separately.

Correction round complete. All five findings fixed, all checks green. Report:

## Changes (exclusive allowed writes only)

1. **`[hidden]` override (`site/assets/css/styles.css`)** — Added a shared `[hidden] { display: none !important; }` rule with a comment explaining why. This makes language-filter cards (`card.hidden` in `catalog.js`) and Nell's inactive `#font-controls` wrapper actually disappear despite `.book { display: flex }` and `.reader-controls { display: flex }`. Not browser-verified by me (image input rejected on this route); coordinator's Playwright re-check will confirm.

2. **Output cleanup safety (`tools/build_catalog.py`)** — `build()` now rejects, *before any cleanup*: the source root, ancestors of the root, `site`/`publications`, and symlinks; and refuses any existing populated directory that is not recognized as generated output (empty dir, `.generated-by-build_catalog` marker, or legacy default-named `_site/` resembling a prior build). Successful builds write the marker immediately after copying. The pre-existing `_site/` was replaced once via the legacy rule and now carries the marker, so future rebuilds are owned.

3. **Nell cover alt text (`site/index.html`)** — Now honestly describes the first-page thumbnail: "thumbnail of the story's opening page, showing the title and first lines of text". No artwork or book files changed.

4. **Default CLI (`tools/build_catalog.py`)** — Bare `python3 tools/build_catalog.py` now defaults to `build` into `_site` and works (verified: builds successfully; previously `AttributeError`).

5. **Metadata-driven tests (`tests/test_catalog.py`)** — Removed the hard-coded three-ID set and fixed totals. `RealRepoTests` now checks the initial releases as a *subset* (INITIAL_IDS) and validates each book's language/layout against declared values; `BuildOutputTests` derives expected counts and catalog IDs from `publications/manifest.json`. Added 6 `OutputSafetyTests` on temp fixtures: source root, ancestor, unrelated populated dir (sentinel file preserved), symlink, rebuild-owned-twice, legacy `_site` replacement. I also made `check_links` validate every `reader.html?book=<id>` against the manifest, so the doc's claim that a bad card ID fails the build is now literally true; `docs/publishing.md` updated to describe the dynamic checks and the output-ownership policy.

## Checks actually run
- `python3 -m unittest discover -s tests -v` — **51 tests, all OK** (including the new output-safety class; other agents' `test_studio.py` untouched and passing).
- `node --check` on `site/assets/js/catalog.js` and `reader.js` — OK.
- `python3 tools/build_catalog.py build` and bare `python3 tools/build_catalog.py` — both build 3 books, copy 9 files (66,321,657 bytes), all manifest/package/hash/link checks pass; `_site/` regenerated with marker.
- Verified built output contains the new CSS rule, corrected alt text, and `.generated-by-build_catalog`.

## Limits
- No browser/Playwright testing performed (per instructions; coordinator owns it). The CSS fix is standard and high-confidence but browser-unverified by me.
- The legacy `_site` allowance is deliberately narrow (default name, `catalog.json` present, top-level entries within the known output shape).

Shared root tasks/handoff/README, commits, and account settings untouched.
