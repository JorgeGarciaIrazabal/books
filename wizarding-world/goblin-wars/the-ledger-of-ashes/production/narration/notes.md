# Audio feasibility and proposed direction

Inspected 2026-10-27 by the voice_director. This is a feasibility record, not a rendered or listened audiobook. Only this notes file was written. The prose is being edited concurrently; no script or audio may be frozen against the present draft.

## Source and coverage

Read the voice-director contract, read-aloud skill, narration documentation, book brief/style/handoff/manifest, existing Nell rendering/checking adapters and cast records, runtime model specification, and earlier local test reports. Current 22-chapter inventory at inspection: `9947eaa9f11b530dc58f0869cdde1b5faedb5a7de4b465cf7dd5ed13a74f8700`; 50,035 whitespace-delimited words. Existing draft export SHA-256: `4933d2b8b2267f2d477c154dc1dc97c0d225bfad2b2ca8d80dfc8ce362ca2e43`. This is not a full manuscript review. Freeze a new inventory after line, copy and production proof.

## Runtime actually checked

- `/tmp/opencode/audio-cpp/build-vk/bin/audiocpp_cli` runs `--help`, `--version`, and `--list-devices`. It reports audio.cpp `c7230db` (2026-10-25), Release, GCC 15.2.0, CPU and Vulkan backends; Radeon 8060S Graphics / RADV GFX1151 and Ryzen AI Max+ 395 CPU are detected. Executable SHA-256: `95936f0997f532376355afdd0eee1de33410dcc4226b4ffab59e24fac45295a6`. The executable lives in a temporary directory, so preserve its build instructions and hash in the eventual render record.
- Model exists at `/home/jgarcairaza/.cache/drama3/Drama-3-GGUF/drama-3-backbone-8bit-experts-Q4_K_S.gguf`, 24,596,497,888 bytes. Prior render record reports SHA-256 `05af716baf78e7c20863b9ccebb3ebdeca9607dd3ea7d0b72c35079e675b212b`; this assignment did not rehash the 23 GiB model or load it for inference.
- `/home/jgarcairaza/code/super_detective_game_2/.venv-tts/bin/python` runs Python 3.12.13 and successfully imports `kokoro`, `faster_whisper`, and `soundfile`. Kokoro and faster-whisper-small.en weights are cached. `ffmpeg` and `ffprobe` are installed under `/usr/bin/`.
- Existing synthetic British narrator reference: `little-weather/standalone/nell-and-the-pocket-sized-storm/production/narration/cast/narrator.wav`, verified SHA-256 `524ac1dfbd990bbc8fff29a43185f4c43024fb447b10125edcff7da31e99353b`. Its cast record identifies Kokoro `bf_emma`, 5.67 s, transcript “The garden was quiet in the late afternoon light, and the kettle had just begun to sing.” This is a usable evaluation reference, not an approved cast for this book.
- Disk had about 837 GiB available. Host memory reported 15 GiB available but swap was nearly full. Previous successful Vulkan tests do not guarantee current resource availability. No fresh synthesis or listening was performed here.

## Format and limits

Use 22 chapter tracks for this reflowable novel, with shorter internal rendering segments. Do not label chapters as pages merely to bypass the fixed-layout validator. `tools/narration.py` explicitly requires a published fixed-layout book; the current web reader and page manifest cannot package this novel unchanged. A standalone local chapter MP3/M4B edition is feasible without publishing or changing the website, followed by an explicit chapter-level reader contract if requested.

The model specification says `max_tokens` counts acoustic frames at about 21.5 frames/s. The old 1,400-token setting therefore permits only about 65 seconds per request, not an entire chapter. Begin with roughly 100–130 words per complete sentence/paragraph segment, max_tokens 1,800–2,200, context 4,096 and chunk_size 4,000 after a pilot confirms these settings. Those are provisional settings, not tested results. Record chapter IDs, ordered segment IDs, source word ranges and hashes. Include each chapter heading once by an explicit policy; concatenate every source word exactly once without overlap, loss or inserted text. Keep tags in production/narration only.

Two existing checker gaps require correction or a new adapter:

1. `build_script_pages.py` checks only tagged pages supplied to it; it does not prove equality of expected and actual page sets. The novel adapter must require exact chapter and segment coverage, nonempty output and source order before comparing stripped text.
2. `check_narration.py` emits ASR text and flags pace/pauses, but does not calculate or fail on a transcript-to-source diff. Add a normalized token diff, report all additions/deletions/substitutions, and adjudicate homophones/names against audio. A zero pause flag is not a fidelity pass. Fail on missing or extra WAVs too.

## Proposed cast and performance

For evaluation, propose a single synthetic adult British narrator, restrained and attentive, around 145–155 wpm, with subtle dialogue changes and no caricatured goblin voice. This is a reversible proposal: narrator identity and separate character voices remain consequential author choices under the skill. A full cast would require many characters, while this runtime accepts speaker indices 0–15; scene-local cast mapping could support it but needs explicit identity/continuity checks and will lengthen both rendering and playback. Do not repurpose Nell's child voices as an adult cast without auditions. Use no celebrity or identifiable person's voice.

Record provisional pronunciations before the pilot: Ragna, Tavin, Sella, Neri, Dorrik, Ilva, Merrok, Kelm, Thorn and the financial terms. Test the first chapter's narrative opening and an exchange with several short replies. Do not alter book text to force pronunciation; use an engine-supported pronunciation layer or a retake method whose spoken words remain exact.

At 140–155 wpm, this 50,035-word draft implies about 5.4–6.0 hours of audio. Prior local reports generated Drama 3 audio near real time; infer a similar several-hour full render, not a promise. ASR checking, failed takes and listening add time. Mono 44.1 kHz 16-bit WAV would occupy roughly 1.7–1.9 GiB; 96 kbps MP3 roughly 230–260 MB. No metered API purchase is needed for this local route; electricity and machine occupation were not costed.

## Licence evidence and publication boundary

The inspected [official Drama 3 licence](https://huggingface.co/fishaudio/drama-3/blob/main/LICENSE) contains Fish Audio Community License v1.0 dated 2026-10-13, despite the model page's shorter metadata label. It allows personal evaluation, has commercial revenue conditions and separate hosted-service terms, restricts unconsented identifiable-person imitation, and requires relevant attribution. Outputs are owned by the user to the extent law permits. Preserve the actual licence with the render record rather than relying on a metadata tag. Local copy `/tmp/opencode/drama3-LICENSE.txt` hash: `733a32442087acbda12ecafe8e71eb8ee5890c89b50ce7ac4ea3777faa3c823e`.

The [Kokoro voice page](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md) identifies the model as Apache-2.0 and lists `bf_emma` as a British female preset. It does not establish an identifiable human target or this book's casting approval. No complete voice-specific rights conclusion was made. This project is unofficial fan fiction; model-output permission does not supply franchise publication rights. No public upload or publication was performed.

## Concrete next action

After final text is stable, create the chapter/segment map and word-exact script validator, record the chosen synthetic reference and licence, then render one 100–130-word excerpt through the existing adapter in an isolated export directory. Existing adapter path is `little-weather/standalone/nell-and-the-pocket-sized-storm/production/narration/tools/render_drama3.py`; its input JSON accepts numbered `pages`, which may serve as internal segment IDs only if a separate chapter map makes that explicit. Use the executable/model above, a synthetic reference, seed 7, Vulkan and context 4,096. Measure duration, run ASR plus the added diff, check pauses and independently listen before expanding. No audio-analysis/listening connector was found in the active tool catalogue; do not equate ASR with listening. The coordinator must arrange actual audition evidence before calling performance reviewed.


## Pilot run after manuscript edit

The coordinator rendered only chapter 1 segment 1 using a provisional synthetic single narrator. See `render.json`, `pilot-segments.json`, and `exports/narration-pilot/` for the exact source, command, audio, transcript and flags. The full private audiobook has **not** been rendered. ASR flagged Ragna/Ragnar plus orthographic and numeric variants; there is 3.041 seconds of silence beginning 2.360 seconds into the sample. Nobody with a listening tool has reviewed it yet. The author was asked to listen to the MP3 before the full render. This is a reflowable chapter audiobook, not the fixed-page public site package.
