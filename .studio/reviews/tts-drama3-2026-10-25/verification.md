# Fish Audio Drama 3 on this machine, tried on Nell

Date: 2026-10-25. Role: studio_director. Author question: can Drama 3 run on
this computer, and does it work for *Nell and the Pocket-Sized Storm*?

**Answer: yes, both.** Drama 3 runs locally on the Radeon 8060S through the
community audio.cpp GGUF port on Vulkan, and it narrated all 30 pages in one
session (13:35 of audio) with text fidelity good enough for a draft, not for a
release. The unquantized checkpoint and the FP8/int4 packages did not run: they
need SGLang-Omni or vLLM-Omni, which are CUDA-oriented and absent here.

## Environment actually used

| Item | Value |
|---|---|
| CPU/APU | AMD Ryzen AI Max+ 395 |
| GPU | Radeon 8060S (RADV GFX1151), Mesa 25.2.8, Vulkan 1.4.318; fp16 yes, bf16 no, integer dot product yes, KHR_coopmat |
| Memory | 96 GiB VRAM carve-out (`mem_info_vram_total` 103079215104), 32 GiB host RAM, 16 GiB GTT |
| Vulkan heap seen by ggml | about 37 GiB, enough for the 23 GiB package |
| Runtime | [audio.cpp](https://github.com/0xShug0/audio.cpp) `c7230db` (2026-10-25), local Release build, backends `cpu,vulkan` |
| Model | `Jmica/Drama-3-GGUF` `drama-3-backbone-8bit-experts-Q4_K_S.gguf`, 22.91 GiB (Q4_K routed experts, Q8_0 backbone, FP16 tower/codec) |
| Reference | `common_voice_en_10119832.wav` (3.9 s, 24 kHz), the clip and transcript published in the Drama 3 model card |
| Text | 30 story pages, 2,047 words, extracted verbatim from the illustrated-v3 export |

Build notes: no passwordless `sudo`, so the Vulkan SDK was extracted to a local
prefix instead of installed. Ubuntu's `glslc` 2025.2 is too old for ggml's
`GL_EXT_integer_dot_product`/`GL_EXT_bfloat16` shaders; LunarG SDK 1.4.363
`glslc` compiled them. CUDA is unavailable; ROCm has no toolkit headers on this
box (`hipcc` absent, `/opt/rocm` absent), so `ENGINE_HIP_STRIX_HALO_OPTIMIZATIONS`
could not be tried.

## Commands

```bash
cmake -B build-vk -DCMAKE_BUILD_TYPE=Release -DENGINE_ENABLE_VULKAN=ON \
  -DENGINE_ENABLE_CUDA=OFF -DENGINE_ENABLE_METAL=OFF -DENGINE_ENABLE_NATIVE_CPU=ON \
  -DAUDIOCPP_MODEL_SET=custom -DAUDIOCPP_MODELS=fish_drama3
cmake --build build-vk --target audiocpp_cli -j 16
./build-vk/bin/audiocpp_cli --task tts --family fish_drama3 --backend vulkan \
  --mode offline --model drama-3-backbone-8bit-experts-Q4_K_S.gguf \
  --voice-ref common_voice_en_10119832.wav \
  --request-option "reference_text=We asked over twenty different people, and they all said it was his." \
  --request-option text_chunk_size=4000 \
  --batch-text-dir requests --out-dir . --max-tokens 1400 --seed 1234 --threads 8
```

The book-side scripts and full rebuild instructions are in
`little-weather/standalone/nell-and-the-pocket-sized-storm/production/tts/`
(`build_narration_pages.py`, `render_drama3.py`, `check_narration.py`,
`notes.md`).

## Measured

- 30/30 pages, one session, about 15 minutes wall including a ~13 s model load;
  27.9 s mean generation per page, 0.954x the duration of its own audio.
- Audio 13:35; 128.8-189.1 wpm (mean 154.9); no pause over 1.5 s; 0/30 pages
  flagged by the mechanical checks.
- Master draft -24.2 LUFS integrated, -2.0 dBFS true peak, 44.1 kHz mono.
- Text fidelity: normalized word diff against the source flagged only
  homophones and onomatopoeia ("rain/reins", "plip/clip", "PIP-pip-PIP",
  "attle/addle"). One genuine lexical error was found and fixed: page 22 ended
  "Grandma let out the breath" at seed 1234; seed 7 reads "Nell let out the
  breath" and is the take in the export.

## Findings that matter for a future edition

1. `text_chunk_size` must exceed a page. At the model's 128-character default, a
   page-16 take inserted a line that is not in the book ("Watch them now.") and
   left an 11 s silence. With `text_chunk_size=4000` two seeds read the page
   correctly. Do not render long-form with the default chunker.
2. Takes are not content-safe by default. Page 22's character swap was only
   caught because every page was transcribed and diffed. Keep that check.
3. Drama 3 clones timbre, not acting. The reference here is a stranger's plain
   speech; a recorded narrator reference in the intended reading voice will
   change the result more than sampler tuning.
4. Single narrator only in this run. `<|speaker:N|>` with two references was
   exercised and both spans rendered, but distinct per-character timbre was not
   verified by measurement. Casting Nell, Grumble and Grandma needs one
   reference recording each and an author decision.
5. The Q4_K GGUF is a community quantisation of the FP8 original, not the
   reference implementation. Higher fidelity would need a CUDA host or a ROCm
   build of SGLang-Omni/vLLM-Omni, neither available here.

## Artifacts

- Audio and checks: `little-weather/standalone/nell-and-the-pocket-sized-storm/exports/tts-drama3-v1/`
  (gitignored): `nell-narration-draft.wav` (sha256
  `4483cbc18bd63b36ecc456377109871fc158a53c3bb299d3f68ee5d52e194818`),
  `nell-narration-draft.mp3`, `pages/page-01..30.wav`, `pages/checks.json`,
  `pages.json`, `batch-manifest.json`.
- Runtime build: `/tmp/opencode/audio-cpp/build-vk/bin/audiocpp_cli`
  (throwaway path; rebuild from the commands above).
- Weights: `/home/jgarcairaza/.cache/drama3/Drama-3-GGUF/` (23 GiB).

## Limits

No human has listened to the output. No loudness normalisation, de-essing, room
tone or noise reduction was applied. Pronunciations, warmth and comic timing are
unassessed; the mechanical checks only prove that the words are roughly present,
the pacing is plausible and no long silences occur. No manuscript, canon,
illustration, EPUB, PDF or published edition changed. Nothing was committed or
published.

## Next action

Listen to `nell-narration-draft.mp3` end to end and mark pages whose delivery is
wrong. Then, if narration should continue, record or choose a narrator reference
(10-30 s) for Nell, decide whether characters get separate voices, and re-render
only the rejected pages with a fixed seed per page.
