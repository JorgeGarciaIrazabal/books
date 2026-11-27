# Narration notes — The Three Paths

- **Engine and version**: Fish Audio Drama 3 via local `audio.cpp` (`04ce54d0d22b29f2982cb6b931331d00c98a1d91`, Vulkan backend) using `tools/drama3.py`.
- **Model file and sha256**: `drama-3-backbone-8bit-experts-Q4_K_S.gguf` (`05af716baf78e7c20863b9ccebb3ebdeca9607dd3ea7d0b72c35079e675b212b`), Fish Audio Community License v1.0.
- **Settings**: `backend=vulkan`, `seed=7` (retakes at `seed=11`), `text_chunk_size=4000`, `max_tokens=1400`, `context_length=4096`, `threads=8`, direction `[warm, expressive adventure storyteller voice]`, `max_words=95` per segment, adaptive inter-segment join padding `sentence_gap_ms=500` / `paragraph_gap_ms=750` (minimum raw join gap increased from `30 ms` in Ch 1 to `500 ms` across every join).
- **Cast**: see `cast.json`. Single synthetic warm American narrator reference (`cast/narrator.wav`, 5.5 s, generated locally with Kokoro-82M ONNX `af_heart`, Apache-2.0, sha256 `75e8edd35b2f86d0309b3aa6925699603e1f562f0934194e9a949874688fdec2`; not a human recording and not an impersonation target).
- **Units rendered**: 87 / 87 segments across 9 chapters (6,876 spoken words; 2,846.464 s / 47:26 assembled audio; 34,166,988 bytes).
- **Checks run**:
  - Word-exact chapter segmentation verified via `tools/drama3.py prepare-chapters` (preserves paragraph breaks inside segments and records `ends_paragraph`; never crosses chapter boundaries).
  - Full 87-segment mechanical check (`tools/drama3.py check`, `faster-whisper` `small.en`, `beam_size=5`, `silencedetect=-40dB/1.5s`): mean 151.8 WPM, 0 flagged.
  - Tag-exclusion and site build checks (`tools/narration.py validate`, `tools/studio.py check`, `tools/build_catalog.py build`, 65 unit tests).
  - **Human listening**: pending author spot-listen on the live audiobook page.
- **Known defects and retakes**:
  - Initial seed-7 pass flagged `u43` (hit `max_tokens=1400`, repeated ending + 48.0 s silence, `sim=0.667`) and an inspection of all non-flagged diffs spotted 1 dropped word (`"Wait!"`) in `u59`.
  - Ran `split-retake` on `u43` at `seed=11` (2 parts, 24.6 s, 163.6 WPM, `sim=1.000`, 0 diffs) and single-unit retake on `u59` at `seed=11` (33.9 s, 148.5 WPM, `sim=0.964`, restoring `"Wait!"`).
  - Remaining ASR differences across the 87 segments are spelling/tokenization splits (`Glassvale` -> `glass veil`, `Mistgate` -> `mist gate`, `Ink-Hounds` -> `inkhounds`, `1` -> `one`, etc.).
- **Rights and publication status**: Outputs owned by the author under Fish Audio Community License v1.0; `"Built with Fish Audio"` attribution is included in `chapters.json` and `site/audiobook-the-three-paths.html`.
- **Next action**: Spot-listen to Chapter 1, Chapter 4 (`u43`), and Chapter 6 (`u59`) on the live audiobook page and retake any line if desired.
