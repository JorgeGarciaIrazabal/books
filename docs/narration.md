# Narration layer

Read-aloud audio is a **separate layer** from the book. The story text is the
book; narration is a performance of it with its own files, its own rights, and
its own review. This document defines where it lives, how it is tagged, how the
web reader plays it, and why the EPUB and PDF can never contain a tag.

## Why a separate layer

A performance tag such as `[sighs]` or `<|speaker:2|>` is direction to a voice, not
prose. If it leaks into `manuscript/`, the export, the EPUB or the PDF, it becomes
a defect in the reading edition and in every downstream file. Keeping narration
in `production/narration/` means:

- the manuscript, export, EPUB and PDF stay byte-clean and unchanged;
- audio can be re-rendered, re-cast or withdrawn without touching the book;
- the same script can feed the website now and a different engine later;
- rights, provenance and voice consent are recorded next to the performance.

Narration is **not canon**. Voice choices, accents and delivery are production
decisions. Pronunciation of canon names may need a canon check, but the tags do
not enter `canon.json`.

## What lives where

| Path | Role | Tracked |
| --- | --- | --- |
| `production/narration/script.md` | Tagged performance script, one block per story page | yes |
| `production/narration/cast.json` | Voices, reference clips, transcripts, provenance, licences | yes |
| `production/narration/cast/*.wav` | Reference clips used for cloning or voice conditioning | yes, when small and licensed |
| `production/narration/render.json` | Engine, model hash, seed, settings, per-page hashes, measured durations | yes |
| `production/narration/notes.md` | How this book's narration was made and what is unresolved | yes |
| `exports/narration/` | Raw per-page WAVs and working masters | no (gitignored) |
| `narration/manifest.json` | Public index of narration packages | yes |
| `narration/<book-id>/narration.json` | Reader manifest: page → file, seconds, hash | yes |
| `narration/<book-id>/page-NN.mp3` | Published audio, mono, 96 kbps | yes |

`narration/` is intentionally separate from `publications/`. A publication file
(PDF, EPUB) is the book artifact; narration is a reading layer that can be
replaced, muted or withdrawn on its own schedule. It also keeps
`tools/build_catalog.py` honest: publications are validated as packages, audio
is validated as audio, and neither can silently pull in the other.

## Script contract

`script.md` is Markdown with one fenced block per page:

```text
## Page 12

```text
<|speaker:1|> [gentle, encouraging] "Just me here," <|speaker:0|> she said.
<|speaker:2|> [straining, hopeful] "PIP!"
```
```

Rules:

1. Every story word appears exactly once, in order. Tags add performance only.
   `tools/build_script_pages.py` strips the tags and fails the build if the
   remaining words differ from the exported page text.
2. One speaker per segment. The narrator (speaker 0) reads every unquoted word,
   including dialogue tags such as `said a cross little voice`.
3. `<|speaker:N|>` values are 0–15 and must match `cast.json` by position.
4. Directions in square brackets apply to the words that follow. Use one per
   speaker turn or emotional beat, not one per line.
5. `[sighs]`, `[laughs]` and `[pause]` are sounds and pauses at that point.
6. Paired delivery tags: `<whisper>`, `<emphasis>`, `<soft>`, `<fast>`, `<slow>`,
   `<stress>`, `<forceful>`.
7. No structural tokens (`<|im_start|>`, `<|voice|>`, and so on); the engine
   rejects them.

## Cast contract

`cast.json` is the machine-readable cast. Each voice records:

- role and speaker index;
- engine and voice identifier (for example `Kokoro-82M` / `bf_emma`);
- the reference clip path, its exact transcript and its sha256;
- how the clip was produced, and its licence;
- a note when the voice is a synthetic stand-in rather than a hired actor.

Hard rules:

- **No identifiable person may be imitated without consent.** A public dataset
  clip is not consent. The Drama 3 licence says the same thing explicitly. The
  Common Voice clip used for the first engine trial is therefore not published;
  only synthetic preset voices or consented recordings ship.
- Every reference must read a **different** sentence. At least one runtime
  (Drama 3 through audio.cpp) collapses voices toward the narrator and appends a
  repeat when every reference shares the same transcript.
- Record the model licence next to the cast. Drama 3 uses the Fish Audio
  Community License (outputs are owned by the user; a hosted TTS service needs a
  separate licence; attribution "Built with Fish Audio" is required when the
  materials are distributed). Kokoro-82M is Apache-2.0, but individual voice
  packs carry their own dataset licences; check the voice before commercial use.

## Default local TTS engine (Fish Audio Drama 3)

On this computer, **Fish Audio Drama 3** via local `audio.cpp` (Vulkan backend)
is the standard TTS engine for all book audio — both fixed-layout page narration
and reflowable chapter audiobooks. Do not fall back to Kokoro-82M or Piper for
final book audio unless the author explicitly asks for a different engine or
Drama 3 is unavailable and reported as a blocker.

Local runtime layout (persistent, outside the repository):

| Component | Default path on this computer | Override env var |
| --- | --- | --- |
| `audiocpp_cli` | `~/.local/bin/audiocpp_cli` (symlink to `~/.local/opt/audio.cpp/build-vk/bin/audiocpp_cli`) | `DRAMA3_CLI` |
| Drama 3 GGUF weights | `~/.cache/drama3/Drama-3-GGUF/drama-3-backbone-8bit-experts-Q4_K_S.gguf` | `DRAMA3_MODEL` |
| Vulkan SDK (`glslc` + headers) | `~/.local/opt/vulkan-sdk/` | — |
| ASR verification | `uv run --with faster-whisper` (`small.en`, CPU int8) | `DRAMA3_WHISPER_PY` |

Verify the local setup at any time with:

```sh
python3 tools/drama3.py doctor
```

If `audiocpp_cli` ever needs a rebuild, build `https://github.com/0xShug0/audio.cpp`
into `~/.local/opt/audio.cpp/build-vk` with `-DENGINE_ENABLE_VULKAN=ON` and
`-DAUDIOCPP_MODEL_SET=custom -DAUDIOCPP_MODELS=fish_drama3`, pointing CMake at
`~/.local/opt/vulkan-sdk` (`glslc`, headers, and `libvulkan.so`), and symlink
`~/.local/bin/audiocpp_cli`.

## Rendering

`tools/drama3.py` is the shared studio driver for Drama 3 (books may still keep
book-specific adapters under `production/narration/tools/` when needed):

### Fixed-layout page narration

```sh
# 1. Strip, validate and group the tagged script into page requests.
python3 tools/drama3.py prepare-pages \
  <book>/production/narration/script.md <book>/exports/<book>.md \
  /tmp/pages.json

# 2. Render with Drama 3 (auto-discovers audiocpp_cli and the cached GGUF).
python3 tools/drama3.py render /tmp/pages.json \
  --out-dir <book>/exports/narration --no-direction \
  --cast <book>/production/narration/cast.json --seed 7

# 3. Check every take (duration, WPM, pauses, faster-whisper transcript diff).
python3 tools/drama3.py check /tmp/pages.json <book>/exports/narration

# 4. Pack the public page audio and manifests.
python3 tools/narration.py pack \
  --book-dir <book> --audio <book>/exports/narration --book-id <book-id>
```

### Reflowable chapter audiobooks

Reflowable books do not have stable page identities, so their audio ships as
chapter MP3s under `site/audio/<book-id>/chapter-NN.mp3` with `chapters.json`
and a dedicated `site/audiobook-<book-id>.html` (or `site/audiobook.html`) page:

```sh
# 1. Split book.json chapters into word-exact segments (<=95 words, never crossing chapters).
python3 tools/drama3.py prepare-chapters \
  --book <book> --out <book>/production/narration/segments.json \
  --script <book>/production/narration/script.md --max-words 95

# 2. Render all segments in chunked Drama 3 sessions (resumable).
python3 tools/drama3.py render <book>/production/narration/segments.json \
  --out-dir <book>/exports/narration-drama3 \
  --cast <book>/production/narration/cast.json --seed 7 --resume

# 3. Re-render any segment that hit max_tokens by splitting at sentence boundaries.
python3 tools/drama3.py split-retake <book>/production/narration/segments.json \
  --pages <N,M> --out-dir <book>/exports/narration-drama3 \
  --cast <book>/production/narration/cast.json --seed 11

# 4. Run mechanical duration, silence, and faster-whisper ASR checks.
python3 tools/drama3.py check <book>/production/narration/segments.json \
  <book>/exports/narration-drama3

# 5. Assemble verified WAVs into mono 96 kbps chapter MP3s, chapters.json, and render.json.
#    Adaptive join padding (--sentence-gap-ms 500, --paragraph-gap-ms 750) prevents rushed
#    transitions after periods at segment joins without double-padding existing silence.
python3 tools/drama3.py assemble-chapters <book>/production/narration/segments.json \
  --audio <book>/exports/narration-drama3 \
  --out site/audio/<book-id> \
  --book-id <book-id> \
  --checks <book>/exports/narration-drama3/checks.json \
  --render-record <book>/production/narration/render.json
```

Rules learned the hard way:

- Keep `text_chunk_size` larger than one page/segment (`4000`). At the engine
  default of 128 characters a take inserted a line and left an 11 s silence.
- Keep chapter segments around `90–95` words when using `max_tokens=1400` so
  takes stay well under the ~65 s cap; use `split-retake` if any segment caps.
- Drama 3 renders each segment with only ~30–140 ms of edge silence, so raw
  concatenation rushes right after a period; `assemble-chapters` and `split-retake`
  now apply adaptive join padding (500 ms sentence, 750 ms paragraph, overridable)
  and add 5 ms micro-fades when an edge has <15 ms of silence.
- Every take needs a transcript diff. End-of-request drift is real and
  seed-dependent; a repeated line at the end of page 1 appeared at seed 1234 and
  not at seed 7.
- A cast of short speaker turns reads slower than a single narrator (about 106–135
  wpm against 155 wpm) because the model leaves 1.3–2.1 s between turns. Decide
  whether that pacing is wanted before rendering a whole book.

## Web reader

`site/assets/js/reader.js` plays narration when the catalog entry has a
`narration` block. The block comes from `narration/manifest.json` through
`tools/build_catalog.py`:

```json
"narration": {
  "manifest": "narration/nell-and-the-pocket-sized-storm/narration.json",
  "pages": 30,
  "seconds": 815.2,
  "credit": "Synthetic narration · Kokoro-82M voices"
}
```

Behavior:

- A **Listen** button appears only for fixed-layout books that have narration.
  It is never autoplayed; audio starts only on a click or key press.
- Playback follows the current page. Turning the page while listening switches
  the audio to that page. When a page's audio ends, the reader turns the page and
  plays the next one, so the story continues without input.
- The same control works in the adaptive text view: the page being read is
  scrolled into view and marked.
- The next page is preloaded silently; the reader never downloads the whole
  book's audio up front.
- If a file is missing or the play promise is rejected, the reader says so, stops,
  and leaves the book readable. Narration failure can never block reading.
- The reader remembers the reading position, not a separate audio position.
  Reopening a book starts with audio off.
- Reduced-motion, focus, 44 px targets, and `aria-pressed` on the Listen button
  follow the same rules as the rest of the reader.

Reflowable books have no stable page identity, so they do not get page audio.
Chapter-level narration for reflowable EPUBs would need its own contract.

## EPUB and PDF stay clean

- Builders read the manuscript and the clean export. They must never read
  `production/narration/script.md` or `narration/`.
- `tools/narration.py validate` scans the manuscript, the export Markdown and the
  built EPUB XHTML for tag tokens (`<|speaker:`, `<|im_`, paired delivery tags).
- `tools/build_catalog.py` scans every published EPUB's XHTML during validation
  and fails the build if a tag token is present. When `pdftotext` is available it
  scans the published PDF text too.
- A tag found in a publication file is a build failure, not a warning.

The EPUB and PDF therefore remain exactly what they were: the story, with no
direction, no speaker numbers, no engine tokens, and no audio dependency. The site
build also refuses audio whose page count disagrees with the page documents the
published EPUB's spine declares, so a page map cannot silently drift from the book.

## Quality gates

| Gate | Who | Evidence |
| --- | --- | --- |
| Script fidelity | `voice_director` | tag-stripped text equals the export, word for word |
| Cast provenance | `voice_director` | `cast.json`: clip, transcript, hash, licence, consent |
| Render provenance | `voice_director` | `render.json`: engine, model hash, seed, settings, per-page hashes |
| Take integrity | independent listener or `reader_advocate` | transcript diff per page, no long pauses, no drift |
| Reading experience | `reader_advocate` (fresh session) | listen-through notes, pacing, pronunciation, comfort |
| Publication exclusion | `production_editor` | EPUB/PDF tag scan, reader behavior, no autoplay |
| Author approval | author | casting and whether narration ships at all |

Mechanical checks cannot certify warmth, comic timing or pronunciation. The
listener review is not optional.
