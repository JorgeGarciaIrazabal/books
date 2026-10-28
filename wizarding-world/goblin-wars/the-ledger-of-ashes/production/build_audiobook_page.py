#!/usr/bin/env python3
"""Generate the public audiobook page from an assembled chapter manifest.

The page uses native audio controls with preload="none". It never autoplays and
contains no performance tags or embedded text.
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
        <h2>{escape(chapter['title'])}</h2>
        <audio controls preload="none" src="{escape(src)}"></audio>
        <p>{clock(chapter['seconds'])} · <a href="{escape(src)}" download>Download this chapter</a></p>
      </li>'''
        )
    total = clock(data["total_seconds"])
    flagged = data.get("asr_flagged_segments", 0)
    total_segments = data.get("total_segments", 0)

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
<style>
  .audio-page {{ max-width: 52rem; }}
  .audio-back {{ display: inline-block; margin: 0 0 1.25rem; font-size: 0.9rem; color: #f2e6c9; }}
  .audio-title {{ font-family: var(--serif); font-size: clamp(1.8rem, 4vw, 2.6rem); line-height: 1.1; margin: 0 0 0.4rem; }}
  .audio-subtitle {{ margin: 0 0 1rem; color: var(--muted); font-size: 1rem; }}
  .audio-notice {{ border: 1px solid var(--line); border-left: 4px solid var(--gold); background: var(--panel); padding: 0.9rem 1rem; border-radius: var(--radius-sm); margin: 1.25rem 0 1.5rem; font-size: 0.92rem; line-height: 1.55; }}
  .audio-links {{ display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 0 0 2rem; }}
  .chapter-audio {{ list-style: none; padding: 0; margin: 0; display: grid; gap: 1rem; }}
  .chapter-audio li {{ background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius); padding: 1rem; }}
  .chapter-audio h2 {{ font-family: var(--serif); font-size: 1.08rem; line-height: 1.3; margin: 0 0 0.6rem; }}
  .chapter-audio audio {{ width: 100%; height: 40px; }}
  .chapter-audio p {{ margin: 0.45rem 0 0; font-size: 0.82rem; color: var(--muted); }}
  .chapter-audio a {{ color: var(--accent-deep); }}
  .audio-foot {{ margin-top: 2rem; font-size: 0.85rem; color: var(--muted); }}
</style>
</head>
<body>
<header class="site-header">
  <div class="wrap audio-page">
    <a class="audio-back" href="index.html">&larr; All books</a>
    <p class="site-kicker">The Goblin Wars, Book One</p>
    <h1 class="audio-title">The Ledger of Ashes</h1>
    <p class="audio-subtitle">Unofficial Wizarding World fan fiction. 22 chapters, {total}.</p>
    <p class="badges">
      <span class="badge badge-lang">English</span>
      <span class="badge">Audiobook</span>
      <span class="badge">Adult</span>
      <span class="badge">Fan fiction</span>
    </p>
  </div>
</header>

<main class="wrap audio-page">
  <p class="audio-notice"><strong>Synthetic narration.</strong> This audio edition was generated locally with Piper (en_GB-jenny_dioco-medium). Every one of the {len(chapters)} chapters was assembled from {total_segments} word-exact segments and machine-checked for coverage and ASR differences. {flagged} of {total_segments} segments carry an ASR or pause flag; they were not heard by a person. An ASR difference is not proof of an audio error. The EPUB and PDF remain the authoritative text. No audio autoplays on this page.</p>

  <div class="audio-links">
    <a class="btn" href="reader.html?book={escape(args.book_id)}">Read online</a>
    <a class="btn btn-ghost" href="publications/{escape(args.book_id)}.epub" download>EPUB</a>
    <a class="btn btn-ghost" href="publications/{escape(args.book_id)}.pdf" download>PDF</a>
  </div>

  <h2>Chapters</h2>
  <ol class="chapter-audio">
{chr(10).join(items)}
  </ol>

  <p class="audio-foot">Narration is a separate performance layer and is not embedded in the EPUB or PDF. The audio files are mono MP3s; each player loads only when you press play.</p>
</main>

<footer class="site-footer">
  <div class="wrap audio-page">
    <p>The Ledger of Ashes is unofficial fan fiction. Harry Potter and the Wizarding World are properties of their respective rights holders; this free fan work is not authorised, endorsed or sponsored by them.</p>
  </div>
</footer>
</body>
</html>
'''
    args.out.write_text(page, encoding="utf-8")
    print(f"wrote {args.out} with {len(chapters)} chapter players")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
