#!/usr/bin/env python3
"""Build or refresh the 10-chapter Fish Audio Drama 3 audiobook, chapters.json,
render record, and static player page for The Quest of the Golden Garbanzo.

Uses the studio-wide Drama 3 pipeline (``tools/drama3.py`` + local ``audio.cpp``
Vulkan runtime). Source chapters are never modified.

Examples:
    # Full Drama 3 render, ASR check, MP3 assembly, and player HTML refresh:
    python3 production/build_audiobook.py

    # Assemble & refresh player HTML from an already-rendered exports directory:
    python3 production/build_audiobook.py --skip-render --skip-check
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from html import escape
from pathlib import Path

BOOK = Path(__file__).resolve().parents[1]
REPO = BOOK.parents[2]
DRAMA3 = REPO / "tools" / "drama3.py"
NARRATION_DIR = BOOK / "production" / "narration"
SEGMENTS_JSON = NARRATION_DIR / "segments.json"
SCRIPT_MD = NARRATION_DIR / "script.md"
CAST_JSON = NARRATION_DIR / "cast.json"
RENDER_RECORD = NARRATION_DIR / "render.json"
WORK_AUDIO = BOOK / "exports" / "narration-drama3"
PUBLIC_AUDIO = REPO / "site" / "audio" / "the-quest-of-the-golden-garbanzo"
PLAYER_HTML = REPO / "site" / "audiobook-the-quest-of-the-golden-garbanzo.html"

CREDIT = (
    "Synthetic narration built with Fish Audio Drama 3 (local audio.cpp Vulkan; "
    "synthetic American narrator reference); not a human performance."
)
VOICE_LABEL = "synthetic warm American narrator (Kokoro af_heart reference, Drama 3 rendering)"
DIRECTION = "[warm, lively storyteller voice]"


def clock(seconds: float) -> str:
    total = int(round(seconds))
    hours, rest = divmod(total, 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return f"{hours} h {minutes:02d} min"
    return f"{minutes}:{secs:02d}"


def build_player_html(meta: dict, manifest: dict) -> str:
    book_id = meta["id"]
    chapters_meta = manifest["chapters"]
    total_seconds = manifest["total_seconds"]
    credit = manifest.get("credit") or CREDIT
    review_status = manifest.get("review_status") or (
        "Coverage, durations, byte sizes, SHA-256 checksums, and faster-whisper ASR "
        "were checked after rendering; human listening review is pending."
    )

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
<meta name="description" content="Chapter audio for The Quest of the Golden Garbanzo, a fun, dramatic Garbanzo Family adventure story. Synthetic narration built with Fish Audio Drama 3.">
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
      <div class="section-heading"><div><p class="audio-eyebrow">GARBANZO FAMILY · STANDALONE</p><h2 id="chapters-title">Chapters</h2></div><span>{len(chapters_meta)} TRACKS</span></div>
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
      <details class="audio-notice"><summary>About this narration</summary><p><strong>Synthetic narration.</strong> {escape(credit)} {escape(review_status)} The EPUB and PDF remain the authoritative text.</p></details>
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


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-words", type=int, default=95)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--batch-size", type=int, default=30)
    parser.add_argument("--skip-prep", action="store_true")
    parser.add_argument("--skip-render", action="store_true")
    parser.add_argument("--skip-check", action="store_true")
    parser.add_argument("--review-status", default=(
        "Coverage, durations, hashes, and faster-whisper ASR checked; human listening review pending."
    ))
    args = parser.parse_args(argv)

    meta = json.loads((BOOK / "book.json").read_text(encoding="utf-8"))

    if not args.skip_prep:
        run([
            sys.executable, str(DRAMA3), "prepare-chapters",
            "--book", str(BOOK),
            "--out", str(SEGMENTS_JSON),
            "--script", str(SCRIPT_MD),
            "--max-words", str(args.max_words),
            "--direction", DIRECTION,
        ])

    if not args.skip_render:
        run([sys.executable, str(DRAMA3), "doctor"])
        run([
            sys.executable, str(DRAMA3), "render", str(SEGMENTS_JSON),
            "--out-dir", str(WORK_AUDIO),
            "--cast", str(CAST_JSON),
            "--direction", DIRECTION,
            "--seed", str(args.seed),
            "--batch-size", str(args.batch_size),
            "--resume",
        ])

    if not args.skip_check:
        run([
            sys.executable, str(DRAMA3), "check",
            str(SEGMENTS_JSON), str(WORK_AUDIO),
        ])

    run([
        sys.executable, str(DRAMA3), "assemble-chapters",
        str(SEGMENTS_JSON),
        "--audio", str(WORK_AUDIO),
        "--out", str(PUBLIC_AUDIO),
        "--book-id", meta["id"],
        "--title", meta["title"],
        "--credit", CREDIT,
        "--voice", VOICE_LABEL,
        "--review-status", args.review_status,
        "--checks", str(WORK_AUDIO / "checks.json"),
        "--render-record", str(RENDER_RECORD),
        "--public-page", f"site/{PLAYER_HTML.name}",
        "--audio-rel-dir", f"site/audio/{meta['id']}",
    ])

    manifest = json.loads((PUBLIC_AUDIO / "chapters.json").read_text(encoding="utf-8"))
    PLAYER_HTML.write_text(build_player_html(meta, manifest), encoding="utf-8")
    print(f"Updated player page -> {PLAYER_HTML}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
