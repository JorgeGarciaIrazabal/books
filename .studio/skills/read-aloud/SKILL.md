---
name: read-aloud
description: Give an author a voice sample, revise a narrator or character voice, or create and check a read-aloud edition.
---

# Read-aloud

“Let me hear the narrator,” “Give the characters distinct voices,” and “Make an
audiobook” are narration requests. A request to change the writing voice belongs
in prose editing. Keep performance directions outside the book text and files.
Use [the narration guide](../../../docs/narration.md) for tooling.

For a voice sample or a change to an existing voice, use one representative
passage with the current text. Provide a listenable clip and say who speaks
and what changes the author can hear. Compare alternatives when requested, using
the same words for both. For a full audiobook, check a sample before rendering
the rest. Ask about tone, pace, pronunciation, or separate character voices
when the decision matters. Keep tags and engine details in production records.

## Before you tag

1. Read the book's `brief.md`, `handoff.md`, `book.json` and the text to be read.
   Use the proofed edition for a full audiobook or the current draft for a sample.
2. Verify the default local TTS engine (**Fish Audio Drama 3** via `audio.cpp`
   Vulkan) is ready on this computer:
   ```sh
   python3 tools/drama3.py doctor
   ```
   Use Drama 3 via `tools/drama3.py` for all book audio on this machine (do not
   substitute Kokoro-82M or Piper for final renders unless the author requests it).
3. Decide the format. Fixed-layout books ship page audio in `narration/<book-id>/`.
   Reflowable books ship chapter-level MP3 audiobooks in `site/audio/<book-id>/`
   with `chapters.json` and a static audiobook player page.
4. Ask the author only for consequential choices: narrator identity, whether
   characters get separate voices, and whether audio is published. Everything
   else is a reversible labeled assumption.
5. Read `docs/narration.md` and copy `templates/book/production/narration/` into
   the book. Set `book.json.narration` to the script, cast, source and render
   paths when applicable.

## Cast

- One voice per speaker index, narrator 0. Every voice needs a reference clip,
  its exact transcript, a hash, provenance and a licence.
- Never imitate an identifiable person without documented consent. A public
  dataset clip is not consent. Synthetic stand-ins are labeled synthetic.
- Every reference must read a **different** sentence. Identical transcripts
  collapse voices toward the narrator in at least one runtime (Drama 3 via
  audio.cpp) and can append a repeated line.
- Check the engine licence before publishing: outputs, redistribution, hosted
  service, attribution.

## Write the script

One fenced block per story page in `production/narration/script.md`.

- The narrator reads every unquoted word, including dialogue tags. Characters
  speak only their quoted lines.
- Directions in square brackets: emotion, intent, pace, addressee. One per turn
  or emotional beat; do not direct every line.
- Supported spans: `<whisper>`, `<emphasis>`, `<soft>`, `<fast>`, `<slow>`,
  `<stress>`, `<forceful>`. Event tags: `[sighs]`, `[laughs]`, `[pause]`.
- Never add, cut or reorder story words. Never write a tag into the manuscript,
  export, EPUB or PDF.

Prove it before rendering:

```sh
# Fixed-layout pages:
python3 tools/drama3.py prepare-pages \
  production/narration/script.md exports/BOOK.md /tmp/pages.json

# Reflowable chapters (word-exact <=95-word segments, never crossing chapters):
python3 tools/drama3.py prepare-chapters \
  --book BOOK_DIR --out production/narration/segments.json \
  --script production/narration/script.md --max-words 95
```

Both verify word-for-word agreement with the book text and fail on any drift.

## Render and check

Render one pilot unit first (`--pages 1`). Inspect duration, pauses, and ASR
transcript (and listen when possible) before rendering the full book. Keep
`text_chunk_size=4000` (the default in `tools/drama3.py`) so Drama 3 never
splits mid-unit.

Then render all units with Drama 3 and check every unit:

```sh
python3 tools/drama3.py render /tmp/pages.json \
  --out-dir exports/narration-drama3 \
  --cast production/narration/cast.json --seed 7 --resume

# If any unit hits max_tokens, split it at sentence boundaries and re-render:
python3 tools/drama3.py split-retake /tmp/pages.json \
  --pages N,M --out-dir exports/narration-drama3 \
  --cast production/narration/cast.json --seed 11

# Check duration, WPM, silences, and faster-whisper ASR diff:
python3 tools/drama3.py check /tmp/pages.json exports/narration-drama3
```

Transcript diff catches inserted, dropped and substituted words. Pause check
catches runaway silence. Neither proves warmth, comic timing or pronunciation.
End-of-request drift is real and seed-dependent: retake a bad unit with a new
seed (`--pages N --seed 11`) and re-check; never assume a clean take because the
words look right.

Record in `render.json`: engine (`audio.cpp` commit + `Fish Audio Drama 3`),
model file and sha256, seed, backend (`vulkan`), chunk size, max tokens, per-unit
or per-chapter hashes and durations, and what was machine-checked versus heard.

## Publish and exclude

```sh
# Fixed-layout page audio:
python3 tools/narration.py pack --book-dir BOOK_DIR --audio EXPORTS_DIR --book-id BOOK_ID

# Reflowable chapter audiobook:
python3 tools/drama3.py assemble-chapters production/narration/segments.json \
  --audio exports/narration-drama3 --out site/audio/BOOK_ID --book-id BOOK_ID \
  --checks exports/narration-drama3/checks.json \
  --render-record production/narration/render.json

# Always validate tag exclusion and rebuild site:
python3 tools/narration.py validate
python3 tools/build_catalog.py build
```

For fixed-layout books, `pack` writes mono MP3s and the reader manifests; the
site build copies them and adds the `narration` block that makes the Listen
control appear. For reflowable books, `assemble-chapters` writes mono 96 kbps
`chapter-NN.mp3` files and `chapters.json` for the static audiobook player page.
Always include `"Built with Fish Audio"` in the public credit line per the Fish
Audio Community License.

The build fails if a performance tag appears in a published EPUB's XHTML or in
the PDF text. Keep it that way: EPUB and PDF remain silent editions unless the
author asks for a separate audio edition.

Do not publish audio without the author's decision and a recorded rights check.
Do not call a synthetic bed a cast. Do not claim a listen that did not happen;
an independent `reader_advocate` listen is separate from the director's checks.
