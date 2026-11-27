# Tagged full-cast pilot for Nell (Drama 3)

Date: 2026-10-26. Follow-up to `.studio/reviews/tts-drama3-2026-10-25/`. The
author asked to add speaker and emotion tags and see how it comes out.

**Result: the tag layer works.** Five synthetic cast voices stay distinct inside
a page, bracketed directions and event tags measurably change delivery, and the
tagged text can be generated from the existing export without touching a word of
the story. The pilot reads slower than the single-narrator draft, and page-level
transcript checks are still mandatory because end-of-request drift is real.

## What was built

| Path | What it is |
|---|---|
| `little-weather/standalone/nell-and-the-pocket-sized-storm/production/tts/tagged-pilot.md` | Tagged script for pages 1-4, 12-13, 16, 18, 21, 26, 30, plus the tag legend, cast table, measured results and listening questions |
| `.../production/tts/build_tagged_pages.py` | Parses the tagged markdown and refuses to emit JSON unless tag removal returns the exact untagged page text |
| `.../production/tts/render_drama3.py` | Extended with `--references` (cast JSON to `<\|speaker:N\|>`), `--no-direction` and `--session` for `fish_drama3.context_length` |
| `.../exports/tts-drama3-pilot-tagged/` | Pilot master WAV/MP3, emotion-probe reel, per-page WAVs, cast and probe JSON (gitignored) |

Tag vocabulary used: `<\|speaker:0..15\|>`, bracketed directions and
`[sighs]`/`[laughs]`/`[pause]`, `<whisper>`, `<emphasis>`, `<soft>`, `<stress>`,
per Fish Audio's Drama 3 documentation.

## Measurement

Environment and runtime are the same as the 2026-10-25 record: audio.cpp
`c7230db`, Vulkan, `drama-3-backbone-8bit-experts-Q4_K_S.gguf`, Radeon 8060S
with the 96 GiB carve-out. Session `context_length=4096` was required because
five references plus 1,400 tokens exceeded the 2,048 default.

- Words: `build_tagged_pages.py` verified all 11 pages word-for-word before
  rendering. After rendering, faster-whisper (small.en, beam 5) matched 9/11
  pages exactly; page 16 only splits "flowerpots", page 26 hears "Brrrumble" as
  "Brumble", and page 18's "PIP-pip-PIP" is present in the waveform but not
  transcribed.
- Voices: five-speaker probe measured 180 / 195 / 241 / 165 / 102 Hz on its five
  lines; page 18 measured 161-180 Hz narration, 134 Hz Grandma, 201 Hz Grumble.
- Timing: 11 pages, 5:58 total, 106-135 wpm. The untagged narration ran 155 wpm.
  Speaker turns carry 1.3-2.1 s of silence; merging narrator paragraphs did not
  change page 1 (29.4 s merged vs 29.6 s line-by-line).
- Levels: -21.9 LUFS integrated, -0.7 dBFS true peak on the pilot; no processing.
- Directions, same sentence and voice: flat 2.60 s / 182 Hz; teasing 2.14 s /
  227 Hz / louder; sincere 3.02 s / 174 Hz; whisper 2.79 s / 33% level;
  angry 2.55 s / 170 Hz; `[laughs]` 4.83 s; `[sighs]` 3.34 s / 155 Hz;
  `<emphasis>`+`<stress>` 3.44 s / 238 Hz.

## Two defects worth recording

1. **Identical reference transcripts break the cast.** Giving all five voices
   the same reference sentence collapsed every line into 125-160 Hz and produced
   an appended repeat. Distinct transcripts per voice restored separation. This
   is a runtime/prompting behaviour, not a property of the book.
2. **End-of-request drift is seed-dependent.** Seed 1234 appended "Nell peered
   into the left boot." after page 1's last line; seed 7 did not. A tagged page
   cannot be trusted without an ASR diff, exactly as in the untagged run.

## Limits

No human listening. The cast is five Kokoro-82M voices, not actors; Nell does not
sound eight and Grandma does not sound old beyond a pitch change. Mr. Moss and
the twins have no lines in the pilot. The dog is narration. The script covers 11
of 30 pages; the remaining 19 have no tags yet. The Q4_K GGUF is still a
community quantisation. Nothing was committed or published; manuscript, canon,
art, EPUB/PDF and site are unchanged.

## Next action

Listen to `exports/tts-drama3-pilot-tagged/nell-tagged-pilot.mp3` and the
`emotion-probes.mp3` reel, then decide three things: how dense the directions
should be, whether 106-135 wpm is acceptable or the turn pauses get trimmed in
post, and who the narrator is. With those answers the remaining 19 pages can be
tagged in the same scheme.
