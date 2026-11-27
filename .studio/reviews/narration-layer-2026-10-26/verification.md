# Narration layer, web read-aloud, and tag exclusion

Date: 2026-10-26. Scope: turn the Drama 3 experiment into a durable studio layer,
ship a working **Listen** control in the browser reader, and guarantee the EPUB
and PDF never carry performance tags.

## What changed

| Area | Paths |
| --- | --- |
| Studio contracts | `.studio/agents/voice_director.md` (new), `.opencode/agents/voice_director.md`, `.codex/agents/voice_director.toml`, `.studio/roster.json`, `studio_director`, `production_editor`, `drafter`, `line_editor`, `copy_editor`, `canon_keeper`, `reader_advocate` contracts |
| Operating docs | `AGENTS.md`, `.studio/workflow.md`, `.studio/craft.md`, `.studio/skills/read-aloud/SKILL.md`, `docs/narration.md`, `docs/publishing.md`, `docs/tooling.md`, `README.md` |
| Templates | `templates/book/book.json` (`narration: null`), `templates/book/AGENTS.md`, `templates/book/production/narration/{script.md,cast.json,notes.md}` |
| Tools | `tools/narration.py` (pack/validate/hash), `tools/build_catalog.py` (narration copy, catalog projection, tag scans, link checks) |
| Site | `site/reader.html`, `site/assets/js/reader.js`, `site/assets/css/styles.css`, `site/index.html` (badge + credit), `tests/test_catalog.py` |
| Book | `book.json` narration block; `production/narration/{script.md,cast.json,render.json,cast/*.wav,tools/*}`; `narration/<book-id>/` package |

## Design decisions

1. **Narration is a separate layer.** Tags live only in `production/narration/`
   and are never written to the manuscript or export. The packer reads rendered
   audio and writes `narration/`, never the book files.
2. **The script is validated, not trusted.** `build_script_pages.py` strips every
   tag and fails unless the remaining words equal the export page text. All 30
   pages pass.
3. **Page audio for fixed-layout books only.** A fixed-layout page has a stable
   spine index. Reflowable books need a chapter-level contract and are out of
   scope rather than half-implemented.
4. **The reader never autoplays.** Listen is a click; the current page drives
   playback; the page turns when a track ends; only the next page is preloaded; a
   failure stops audio and leaves the book readable.
5. **The EPUB and PDF are silent editions.** The build scans every published
   EPUB's XHTML and, when `pdftotext` is available, the PDF text for performance
   tags and fails on a hit. Narration assets are never copied into a publication.
6. **Rights are part of the layer.** `cast.json` records every reference clip,
   transcript, hash, engine and licence. The Common Voice clone from the first
   engine trial was not published; the shipped cast is synthetic Kokoro-82M. The
   reader and catalogue credit "built with Fish Audio Drama 3" and the synthetic
   voices.
7. **One new specialist.** `voice_director` owns script, cast, render and take
   checks. `reader_advocate` listens independently; `production_editor` proves the
   package and the exclusion. The author keeps casting and publication decisions.

## Verification actually run

- `python3 -m unittest discover -s tests`: **57 tests pass**, including five new
  narration cases: a valid package builds, a hash mismatch fails, narration on a
  reflowable book fails, and a performance tag inside an EPUB fails.
- `python3 tools/narration.py validate`: 1 narration book, 30 page files, hashes
  and durations consistent; **3 EPUBs and 3 PDFs scanned, no tag found**; the
  script/export word check passes.
- `python3 tools/build_catalog.py build`: 3 books, 9 publication files, 32
  narration files (index, reader manifest, 30 MP3s), all package/hash/link checks
  pass. The catalog entry for Nell carries `narration` with the manifest URL,
  page count, seconds and credit; the other two books have none.
- Browser, headless Chrome at 390×844 and 1440×900 via
  `.studio/reviews/narration-layer-2026-10-26/browser-check.mjs`: **17 checks, 0
  page errors**. Covered: the bar appears only for the narrated book and stays hidden for a book without narration; no MP3
  requested before a click; Listen starts page 1; a page turn switches the track
  to page 2; a track end advances to page 3; the text view marks the narrated page;
  pause clears the pressed state; blocked audio reports and reading stays usable;
  no horizontal overflow at 1440; a real browser requests `page-01.mp3` and
  preloads `page-02.mp3`.
- Audio: 30 pages, 16.8 min, 12.1 MB at 96 kbps mono, -22.4 LUFS, -0.7 dBFS peak.
  28/30 pages transcribe word for word; page 18's high "PIP-pip-PIP" is audible
  but not transcribed; page 24 gains an ASR "pip". Pages 7, 17 and 27 were
  retaken at seed 11 after the first pass repeated or truncated content.

## Limits and not-done

- **No human has listened to the 30-page set.** The synthetic cast is a stand-in,
  not casting. Warmth, comic timing, pronunciation and bedtime comfort are
  unassessed.
- Pacing is 100–169 wpm (mean 123) because speaker turns carry 1.3–2.1 s of
  silence. Whether to trim pauses in post is an author decision.
- The dog and the twins have no voices; Nell and Grandma differ mainly by pitch.
- Reflowable books have no read-aloud. EPUB media overlays were not requested and
  are not implemented.
- Browser QA used headless Chrome with emulated viewports, not physical devices or
  every browser. Accessibility was not certified.
- Nothing was committed or published in this pass. The audio ships in the local
  site build; publication remains the author's call.

## Evidence

- `browser-check.mjs`, `browser-report.json`, three screenshots in this folder.
- `metrics.json` for counts, hashes and timings.
- Book record: `little-weather/standalone/nell-and-the-pocket-sized-storm/production/narration/`
  and `exports/narration-v1/checks.json`.
- Public package: `narration/nell-and-the-pocket-sized-storm/`.
