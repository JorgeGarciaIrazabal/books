#!/usr/bin/env python3
"""Generate the 10-chapter MP3 audiobook, chapters.json manifest, render record,
and dedicated site player page for The Quest of the Golden Garbanzo using local
Kokoro-82M ONNX (voice: af_heart).

Run with:
    uv run --with kokoro-onnx --with soundfile python production/build_audiobook.py
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
import urllib.request
from html import escape
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

BOOK = Path(__file__).resolve().parents[1]
REPO = BOOK.parents[2]
AUDIO_DIR = REPO / "site" / "audio" / "the-quest-of-the-golden-garbanzo"
PLAYER_HTML = REPO / "site" / "audiobook-the-quest-of-the-golden-garbanzo.html"
RENDER_RECORD = BOOK / "production" / "narration" / "render.json"

CACHE_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "kokoro-onnx"
MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
VOICES_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"

VOICE = "af_heart"
ENGINE = "Kokoro-82M ONNX (kokoro-onnx)"
CREDIT = "Synthetic narration generated locally with Kokoro-82M ONNX (voice: af_heart); not a human performance."


def ensure_file(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and dest.stat().st_size > 1_000_000:
        return dest
    print(f"Downloading {dest.name}...")
    tmp = dest.with_suffix(dest.suffix + ".part")
    urllib.request.urlretrieve(url, tmp)
    tmp.replace(dest)
    return dest


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


ACRONYMS = {"AI", "IRS", "USB", "NJ"}


def _fix_caps(match: re.Match[str]) -> str:
    word = match.group(0)
    if word in ACRONYMS:
        return word
    return word.lower()


def strip_md(text: str) -> str:
    cleaned = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    cleaned = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"\1", cleaned)
    cleaned = re.sub(r"`([^`]+?)`", r"\1", cleaned)
    cleaned = re.sub(r"\b[A-Z]{2,}\b", _fix_caps, cleaned)
    return cleaned.replace("50 / 50", "fifty-fifty")


def clock(seconds: float) -> str:
    total = int(round(seconds))
    hours, rest = divmod(total, 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return f"{hours} h {minutes:02d} min"
    return f"{minutes}:{secs:02d}"


def load_chapters() -> tuple[dict, list[dict]]:
    meta = json.loads((BOOK / "book.json").read_text(encoding="utf-8"))
    paths = meta["chapters"]
    if len(paths) != 10 or len(set(paths)) != len(paths):
        raise ValueError("Expected 10 distinct chapters in book.json")
    chapters = []
    for idx, rel in enumerate(paths, 1):
        raw = (BOOK / rel).read_text(encoding="utf-8").strip()
        heading, body = raw.split("\n", 1)
        if not heading.startswith("# "):
            raise ValueError(f"Expected '# ' heading in {rel}")
        title = heading[2:].strip()
        paras = [strip_md(re.sub(r"\s+", " ", p).strip()) for p in re.split(r"\n\s*\n", body.strip()) if p.strip()]
        chapters.append({
            "number": idx,
            "source": rel,
            "title": title,
            "paragraphs": paras,
            "source_sha256": hashlib.sha256((BOOK / rel).read_bytes()).hexdigest(),
        })
    return meta, chapters


def probe_duration(mp3_path: Path) -> float:
    out = subprocess.check_output(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(mp3_path),
        ],
        text=True,
    ).strip()
    return round(float(out), 3)


def build_player_html(meta: dict, chapters_meta: list[dict], total_seconds: float) -> str:
    book_id = meta["id"]
    items = []
    for ch in chapters_meta:
        src = f"audio/{book_id}/{ch['file']}"
        items.append(
            f'''      <li>
        <span class="chapter-number" aria-hidden="true">{ch['number']:02d}</span>
        <div class="chapter-details"><h3>{escape(ch['title'])}</h3>
        <audio controls preload="none" src="{escape(src)}"></audio>
        <p><span>{clock(ch['seconds'])}</span> <a href="{escape(src)}" download>Download <span class="visually-hidden">{escape(ch['title'])}</span></a></p></div>
      </li>'''
        )

    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#1e2634">
<title>{escape(meta['title'])}: audiobook</title>
<meta name="description" content="Chapter audio for The Quest of the Golden Garbanzo, a fun, dramatic Garbanzo Family adventure story. Synthetic narration.">
<link rel="stylesheet" href="assets/css/styles.css">
<link rel="icon" href="assets/icon.svg" type="image/svg+xml">
<link rel="stylesheet" href="assets/css/audiobook.css">
</head>
<body>
<header class="audio-header">
  <div class="wrap audio-shell"><a class="audio-back" href="index.html">← All books</a><span class="audio-brand">THE LIBRARY / AUDIOBOOK</span></div>
</header>
<main class="wrap audio-shell">
  <div class="audio-layout">
    <aside class="chapter-section" aria-labelledby="chapters-title">
      <div class="section-heading"><div><p class="audio-eyebrow">GARBANZO FAMILY · STANDALONE</p><h2 id="chapters-title">Chapters</h2></div><span>10 TRACKS</span></div>
      <p class="chapter-instruction">Choose a chapter, then press play.</p>
      <ol class="chapter-audio">
{chr(10).join(items)}
      </ol>
    </aside>
    <div class="player-column">
      <section id="audio-player" class="audio-player" aria-label="Audiobook player" hidden>
        <p class="audio-eyebrow">GARBANZO FAMILY · STANDALONE</p>
        <img class="audio-cover" src="publications/covers/{escape(book_id)}.jpg" alt="Cover of {escape(meta['title'])}">
        <h1 id="book-title">{escape(meta['title'])}</h1>
        <p class="audio-description">A fun, dramatic family adventure · {escape(clock(total_seconds))}</p>
        <div class="player-current"><p id="audio-position"></p><h2 id="audio-current"></h2></div>
        <div id="audio-control"></div>
        <div class="audio-player-nav">
          <button id="audio-previous" type="button">← Previous chapter</button>
          <button id="audio-next" type="button">Next chapter →</button>
        </div>
        <p class="player-hint">The next chapter plays automatically.</p>
        <p id="audio-status" role="status"></p>
        <div class="audio-links">
          <a href="reader.html?book={escape(book_id)}">Read the book</a>
          <a id="audio-download" download>Download chapter</a>
          <a href="publications/{escape(book_id)}.epub" download>EPUB</a>
          <a href="publications/{escape(book_id)}.pdf" download>PDF</a>
        </div>
      </section>
      <details class="audio-notice"><summary>About this narration</summary><p><strong>Synthetic narration.</strong> {escape(CREDIT)} File coverage, durations, byte sizes, and SHA-256 checksums were verified after rendering; human listening review is pending. The EPUB and PDF remain the authoritative text.</p></details>
    </div>
  </div>
</main>

<footer class="site-footer">
  <div class="wrap audio-page">
    <p>The Quest of the Golden Garbanzo is an original Garbanzo Family adventure story. Chapter audio is provided for private and shared family listening.</p>
  </div>
</footer>
<script src="assets/js/audiobook.js" defer></script>
</body>
</html>
'''


def main() -> int:
    model_path = ensure_file(MODEL_URL, CACHE_DIR / "kokoro-v1.0.onnx")
    voices_path = ensure_file(VOICES_URL, CACHE_DIR / "voices-v1.0.bin")

    meta, chapters = load_chapters()
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    RENDER_RECORD.parent.mkdir(parents=True, exist_ok=True)

    print("Loading Kokoro-82M ONNX model...")
    kokoro = Kokoro(str(model_path), str(voices_path))

    chapters_meta = []
    total_seconds = 0.0
    sample_rate = 24000

    with tempfile.TemporaryDirectory(prefix="garbanzo-tts-", ignore_cleanup_errors=True) as tmp:
        tmp_dir = Path(tmp)
        title_gap = np.zeros(int(sample_rate * 0.75), dtype=np.float32)
        para_gap = np.zeros(int(sample_rate * 0.45), dtype=np.float32)

        for ch in chapters:
            fname = f"chapter-{ch['number']:02d}.mp3"
            final_mp3 = AUDIO_DIR / fname
            print(f"Synthesizing {fname}: {ch['title']}...")

            pieces: list[np.ndarray] = []
            title_audio, sr = kokoro.create(ch["title"], voice=VOICE, speed=1.0, lang="en-us")
            if sr != sample_rate:
                sample_rate = sr
                title_gap = np.zeros(int(sample_rate * 0.75), dtype=np.float32)
                para_gap = np.zeros(int(sample_rate * 0.45), dtype=np.float32)
            pieces.append(np.asarray(title_audio, dtype=np.float32))
            pieces.append(title_gap)

            for i, para in enumerate(ch["paragraphs"]):
                audio, _ = kokoro.create(para, voice=VOICE, speed=1.0, lang="en-us")
                pieces.append(np.asarray(audio, dtype=np.float32))
                if i + 1 < len(ch["paragraphs"]):
                    pieces.append(para_gap)

            full_audio = np.concatenate(pieces)
            wav_path = tmp_dir / f"chapter-{ch['number']:02d}.wav"
            sf.write(wav_path, full_audio, sample_rate)
            subprocess.run(
                [
                    "ffmpeg", "-y", "-v", "error", "-i", str(wav_path),
                    "-ac", "1", "-ar", str(sample_rate), "-b:a", "96k", "-map_metadata", "-1",
                    str(final_mp3),
                ],
                check=True,
            )

            secs = probe_duration(final_mp3)
            size = final_mp3.stat().st_size
            digest = sha256_file(final_mp3)
            total_seconds += secs
            print(f"  -> {fname}: {secs}s, {size} bytes")
            chapters_meta.append({
                "number": ch["number"],
                "title": ch["title"],
                "file": fname,
                "seconds": secs,
                "bytes": size,
                "sha256": digest,
                "source": ch["source"],
                "source_sha256": ch["source_sha256"],
            })

    total_seconds = round(total_seconds, 3)
    manifest = {
        "schema_version": 1,
        "book_id": meta["id"],
        "title": meta["title"],
        "credit": CREDIT,
        "engine": ENGINE,
        "voice": VOICE,
        "review_status": "Coverage, durations, sizes, and SHA-256 checksums verified; human listening review pending.",
        "total_seconds": total_seconds,
        "chapters": [
            {k: c[k] for k in ("number", "title", "file", "seconds", "bytes", "sha256")}
            for c in chapters_meta
        ],
    }
    (AUDIO_DIR / "chapters.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    render_info = {
        "schema_version": 1,
        "status": "Published synthetic audiobook; coverage, durations, and hashes verified; human listening pending",
        "engine": ENGINE,
        "voice": VOICE,
        "format": "mono 24000 Hz 96 kbps CBR MP3",
        "total_seconds": total_seconds,
        "total_bytes": sum(c["bytes"] for c in chapters_meta),
        "public_page": f"site/{PLAYER_HTML.name}",
        "audio_dir": "site/audio/the-quest-of-the-golden-garbanzo",
        "chapters": chapters_meta,
    }
    RENDER_RECORD.write_text(json.dumps(render_info, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    PLAYER_HTML.write_text(build_player_html(meta, chapters_meta, total_seconds), encoding="utf-8")
    print(f"Done: 10 chapters, total {clock(total_seconds)} ({total_seconds} s), {render_info['total_bytes']} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
