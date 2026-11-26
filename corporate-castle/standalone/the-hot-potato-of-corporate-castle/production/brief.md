# Production Brief — The Hot Potato of Corporate Castle

- **Current published release**: **Prologue Preview Edition** (authorized by author `2026-11-26`: *"can you publish just the prologue for now?"*). Contains strictly `manuscript/000-prologue-the-hot-potato-of-corporate-castle.md` (SHA-256 `e90e98259a5bc665f082af6df8597f61b5a631d21fb30105a7d7be73e2886a4d`); unfinished `001-the-reluctant-steward.md` is intentionally excluded.
- **Working title**: *The Hot Potato of Corporate Castle*
- **Build script**: `production/build_edition.py` (ReportLab + Pillow via `uv run --with reportlab --with pillow`).
- **Artifacts staged in `publications/`**:
  - `publications/the-hot-potato-of-corporate-castle.epub` (`50964` bytes, SHA-256 `d0284441fc0683572324c2b2329f438d0fc0f6cfc193e22e5a8709caa12adf41`, reflowable EPUB 3)
  - `publications/the-hot-potato-of-corporate-castle.pdf` (`169678` bytes, SHA-256 `c30a4181f3779d1802bc573378035673106162b0f36880ae85364af01afe160f`, 4 pages, 6×9 reading trim)
  - `publications/covers/the-hot-potato-of-corporate-castle.jpg` (`66971` bytes, SHA-256 `c666c4f71a3f751987e2f5a4f372d6d441abf03df19540d6f4c0f0d87cab91cd`, 720×1080 typographic cover)
- **Visual proof coverage**: Cover (`page-1.png`) and body pages (`page-2.png`–`page-4.png`) rendered at 120 dpi via `pdftoppm` and visually inspected; zero orphan lines, zero clipped text, zero performance tags.
- **Audiobook (Prologue Preview)**:
  - Rendered locally with **Fish Audio Drama 3** (`audio.cpp` Vulkan, synthetic `af_heart` narrator reference) across 11 word-exact Prologue segments (seed 7, plus seed 11 retakes for `u02` and `u10`; 0 flagged, 0 word errors, 0.0s runaway pauses, mean 155.6 wpm).
  - Assembled to `site/audio/the-hot-potato-of-corporate-castle/chapter-01.mp3` (`5:05`, `304.878s`, `3,659,660` bytes, mono 24 kHz 96 kbps CBR MP3) + `chapters.json` and `site/audiobook-the-hot-potato-of-corporate-castle.html` (with `"Built with Fish Audio"` attribution and synthetic narration disclosure; EPUB and PDF verified tag-free).
- **Author / rights & privacy (`DEC-CC-0004`)**: Owned by the human author; strictly fictionalized. Published live on GitHub Pages (`origin/main`).
