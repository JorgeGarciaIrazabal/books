# Narration notes — The Quest of the Golden Garbanzo

- **Engine and version**: Fish Audio Drama 3 via local `audio.cpp` (`04ce54d0d22b`, Vulkan backend, Radeon 8060S / RADV GFX1151) using `tools/drama3.py`.
- **Model file and sha256**: `drama-3-backbone-8bit-experts-Q4_K_S.gguf` (`05af716baf78e7c20863b9ccebb3ebdeca9607dd3ea7d0b72c35079e675b212b`), Fish Audio Community License v1.0.
- **Settings**: `backend=vulkan`, `seed=7` (retakes at `seed=11`), `text_chunk_size=4000`, `max_tokens=1400`, `context_length=4096`, `threads=8`, direction `[warm, lively storyteller voice]`, `max_words=95` per segment.
- **Cast**: see `cast.json`. Single synthetic warm American narrator reference (`cast/narrator.wav`, 5.5 s, generated locally with Kokoro-82M ONNX `af_heart`, Apache-2.0; not a human recording and not an impersonation target).
- **Units rendered**: 97 / 97 segments across 10 chapters (8,252 spoken words; 0 capped segments).
- **Checks run**:
  - Word-exact chapter segmentation verified via `tools/drama3.py prepare-chapters` (never crosses chapter boundaries; Markdown italics stripped without altering words).
  - Full 97-segment mechanical check (`tools/drama3.py check`, `faster-whisper` `small.en`, `beam_size=5`, `silencedetect=-40dB/1.5s`).
  - Tag-exclusion and site build checks (`tools/narration.py validate`, `tools/build_catalog.py build`, 60 unit tests).
  - **Human listening**: not performed yet.
- **Known defects and retakes**:
  - Initial seed-7 pass flagged 5 units: `u26` (7.2 s silence), `u35` (18.5 s silence + 14-word drop), `u47` (4.5 s silence), `u81` (222.8 wpm on 15-word chapter ending), and `u83` (`sim=0.889`, ASR homophones/digits such as `zipping`, `12`, `3`, `14`, `sparkle wing`). A full diff scan also spotted a 1-word drop (`waist`) in `u80`.
  - Retook `u26, u35, u47, u80, u81` at `seed=11`: all 5 passed with 0 flags (`u26` pause 2.4 s / 1.000 sim; `u35` pause 0.0 s / 0.989 sim with all 14 missing words restored, though ASR hears `"moving"` as `"everything"`; `u47` pause 0.0 s / 0.984 sim; `u80` 1.000 sim; `u81` 201.9 wpm / 1.000 sim).
  - Spanish terms (`Valladolid`, `cocido madrileño`, `entrega de llaves`, `Señor`, `Río`, `Sofía`, `Buenos días`) rendered intelligibly in Drama 3; human spot-listening is still recommended for accent and family-name pronunciation.
- **Rights and publication status**: Outputs owned by the author under Fish Audio Community License v1.0; `"Built with Fish Audio"` attribution is included in `chapters.json` and `site/audiobook-the-quest-of-the-golden-garbanzo.html`. Published to `origin/main` per author authorization.
- **Next action**: Spot-listen to Chapter 1, Chapter 4 (segment 35), and Chapter 10 on the live audiobook page and retake any line if desired.
