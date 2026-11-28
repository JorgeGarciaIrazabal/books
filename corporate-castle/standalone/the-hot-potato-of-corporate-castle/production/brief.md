# Production Brief — The Hot Potato of Corporate Castle

- **Current published release**: **Preview Edition — Prologue & Chapter One** (authorized by author `2026-11-27`: *"publish what we have so far"*). Contains `manuscript/000-prologue-the-hot-potato-of-corporate-castle.md` (SHA-256 `ada4c4e0cfb371f721a945d25ef99d809600f351dad747873c3e7ebc009db0ad`) and `manuscript/001-the-reluctant-steward.md` (SHA-256 `7f47d72568ac89fa3d53c85832ee9fd599cd161c6bf617f16a6569baaae17dde`).
- **Working title**: *The Hot Potato of Corporate Castle*
- **Build script**: `production/build_edition.py` (ReportLab + Pillow via `uv run --with reportlab --with pillow`).
- **Artifacts staged in `publications/`**:
  - `publications/the-hot-potato-of-corporate-castle.epub` (`68333` bytes, SHA-256 `31b1baf9a2f41d5e0a67826127811077979b45e04448838c4dfa4cc3103d15da`, reflowable EPUB 3)
  - `publications/the-hot-potato-of-corporate-castle.pdf` (`253377` bytes, SHA-256 `d9838873e13926f577b47d86c2c3cde6beadd3709b69339deb74d5588c9c507d`, 19 pages, 6×9 reading trim)
  - `publications/covers/the-hot-potato-of-corporate-castle.jpg` (`71035` bytes, SHA-256 `1208b56d4d83e0d4dbb25fe55355f156c9c80119dcd6be99ba0ff860cfaeec95`, 720×1080 typographic cover)
- **Visual proof coverage**: Cover (`page-1.png`) and body pages (`page-2.png`–`page-4.png`) rendered at 120 dpi via `pdftoppm` and visually inspected; zero orphan lines, zero clipped text, zero performance tags.
- **Audiobook (Prologue Preview)**:
  - Rendered locally with **Fish Audio Drama 3** (`audio.cpp` Vulkan, synthetic `af_heart` narrator reference) across 11 word-exact Prologue segments (seed 7, plus seed 11 retakes for `u02` and `u10`; 0 flagged, 0 word errors, 0.0s runaway pauses, mean 155.6 wpm).
  - Assembled to `site/audio/the-hot-potato-of-corporate-castle/chapter-01.mp3` (`5:05`, `304.878s`, `3,659,660` bytes, mono 24 kHz 96 kbps CBR MP3) + `chapters.json` and `site/audiobook-the-hot-potato-of-corporate-castle.html` (with `"Built with Fish Audio"` attribution and synthetic narration disclosure; EPUB and PDF verified tag-free).
- **Author / rights & privacy (`DEC-CC-0004`)**: Owned by the human author; strictly fictionalized. Published live on GitHub Pages (`origin/main`).
