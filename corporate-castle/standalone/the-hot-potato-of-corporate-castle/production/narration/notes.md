# Narration Notes — The Hot Potato of Corporate Castle (Prologue Preview)

- **Scope**: Prologue only (`manuscript/000-prologue-the-hot-potato-of-corporate-castle.md`, 11 segments, 774 words). Draft Chapter 1 is excluded.
- **Engine**: Local **Fish Audio Drama 3** via `audio.cpp` (Vulkan backend) and `tools/drama3.py`.
- **Cast**: Single synthetic American narrator reference (`cast/narrator.wav`, Kokoro-82M `af_heart` conditioning clip, labeled synthetic; no identifiable human imitated).
- **Direction**: `[clear, poised, dryly witty storyteller voice]`.
- **Pronunciation watch list**: `Sarai`, `Okta`, `ER` (initialism "E-R"), `PIP` ("pip" or "P-I-P"), `Slack-runes`, `Volun-telling`. Initial seed-7 render produced two stumbles caught by faster-whisper ASR (`u02` *"full-blown"* and `u10` *"Volun-telling"*); both were retaken cleanly at seed 11 (`u02` transcribed *"full-blown"*, `u10` transcribed *"volantelling"*). All 11 units passed with 0 flags, 0.0s runaway pauses, mean 155.6 wpm; human listening review pending.
- **Output**: Assembled to `site/audio/the-hot-potato-of-corporate-castle/chapter-01.mp3` (`5:05`, `3,659,660` bytes) + `chapters.json` and `site/audiobook-the-hot-potato-of-corporate-castle.html`.
- **Separation**: Performance tags and audio live strictly inside `production/narration/`, `exports/narration-drama3/`, and `site/audio/the-hot-potato-of-corporate-castle/`. The manuscript, EPUB, and PDF contain zero performance tags.
