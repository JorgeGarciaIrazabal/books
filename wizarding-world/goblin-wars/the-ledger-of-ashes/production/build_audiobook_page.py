#!/usr/bin/env python3
"""Generate the public audiobook page from an assembled chapter manifest.

The page uses native audio controls and starts only after a listener action.
It contains no performance tags or embedded text.
"""
from __future__ import annotations

import argparse
import json
from html import escape
from pathlib import Path


def clock(seconds: float) -> str:
    total = int(round(seconds))
    hours, rest = divmod(total, 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return f"{hours} h {minutes:02d} min"
    return f"{minutes}:{secs:02d}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("chapters", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--book-id", default="the-ledger-of-ashes")
    args = parser.parse_args()

    data = json.loads(args.chapters.read_text(encoding="utf-8"))
    if data.get("book_id") != args.book_id:
        raise SystemExit("Chapter manifest book_id does not match --book-id")
    chapters = data["chapters"]
    if len(chapters) != 22:
        raise SystemExit(f"expected 22 chapters, found {len(chapters)}")
    if [c["number"] for c in chapters] != list(range(1, 23)):
        raise SystemExit("chapter numbers are not contiguous")

    items = []
    for chapter in chapters:
        src = f"audio/{args.book_id}/{chapter['file']}"
        items.append(
            f'''      <li>
        <span class="chapter-number" aria-hidden="true">{chapter['number']:02d}</span>
        <div class="chapter-details"><h3>{escape(chapter['title'])}</h3>
        <audio controls preload="none" src="{escape(src)}"></audio>
        <p><span>{clock(chapter['seconds'])}</span> <a href="{escape(src)}" download>Download <span class="visually-hidden">{escape(chapter['title'])}</span></a></p></div>
      </li>'''
        )
    total = clock(data["total_seconds"])
    flagged = data.get("asr_flagged_segments")
    total_segments = data.get("total_segments", 0)
    review = data.get("review_status", "Coverage checked; human listening pending.")
    if flagged is not None:
        review = f"{review} {flagged} of {total_segments} segments carry an ASR or pause flag; they were not heard by a person."
    credit = data.get("credit", "Synthetic narration generated locally; not a human performance.")

    page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#1e2634">
<title>The Ledger of Ashes: audiobook</title>
<meta name="description" content="Chapter audio for The Ledger of Ashes, an unofficial Wizarding World fan novel. Synthetic narration.">
<link rel="stylesheet" href="assets/css/styles.css">
<link rel="icon" href="assets/icon.svg" type="image/svg+xml">
<link rel="stylesheet" href="assets/css/audiobook.css">
</head>
<body>
<header class="audio-header">
  <div class="wrap audio-shell"><a class="audio-back" href="index.html">← All books</a><span class="audio-brand">THE LIBRARY / AUDIOBOOK</span></div>
</header>
<main class="wrap audio-shell">
  <section class="audio-hero" aria-labelledby="book-title">
    <img class="audio-cover" src="publications/covers/the-ledger-of-ashes.jpg" alt="Cover of The Ledger of Ashes">
    <div class="audio-intro">
      <p class="audio-eyebrow">THE GOBLIN WARS · BOOK ONE</p>
      <h1 id="book-title">The Ledger of Ashes</h1>
      <p class="audio-description">An unofficial Wizarding World fan novel</p>
      <p class="audio-meta">22 chapters <span>•</span> {total} <span>•</span> English</p>
      <div class="audio-links">
        <a class="audio-link-primary" href="reader.html?book={escape(args.book_id)}">Read the book <span aria-hidden="true">↗</span></a>
        <a href="publications/{escape(args.book_id)}.epub" download>EPUB</a>
        <a href="publications/{escape(args.book_id)}.pdf" download>PDF</a>
      </div>
    </div>
  </section>
  <div class="audio-layout">
    <section class="chapter-section" aria-labelledby="chapters-title">
      <div class="section-heading"><div><p class="audio-eyebrow">THE COMPLETE AUDIOBOOK</p><h2 id="chapters-title">Chapters</h2></div><span>22 TRACKS</span></div>
      <p class="chapter-instruction">Choose any chapter to start listening.</p>
      <ol class="chapter-audio">
{chr(10).join(items)}
      </ol>
    </section>
    <aside class="player-column">
      <section id="audio-player" class="audio-player" aria-label="Audiobook player" hidden>
        <div class="player-top"><span class="player-dot"></span> SELECTED CHAPTER <span id="audio-position"></span></div>
        <h2 id="audio-current"></h2>
        <p class="player-book">The Ledger of Ashes</p>
        <div id="audio-control"></div>
        <div class="audio-player-nav">
          <button id="audio-previous" type="button">← Previous</button>
          <button id="audio-next" type="button">Next →</button>
        </div>
        <p class="player-hint">Chapters play continuously after you start listening.</p>
        <p id="audio-status" role="status"></p>
      </section>
      <details class="audio-notice"><summary>About this narration</summary><p><strong>Synthetic narration.</strong> {escape(credit)} This edition was assembled from {total_segments} word-exact segments. {escape(review)} The EPUB and PDF remain the authoritative text.</p></details>
    </aside>
  </div>
</main>

<footer class="site-footer">
  <div class="wrap audio-page">
    <p>The Ledger of Ashes is unofficial fan fiction. Harry Potter and the Wizarding World are properties of their respective rights holders; this free fan work is not authorised, endorsed or sponsored by them.</p>
  </div>
</footer>
<script src="assets/js/audiobook.js" defer></script>
</body>
</html>
'''
    args.out.write_text(page, encoding="utf-8")
    print(f"wrote {args.out} with {len(chapters)} chapter players")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
