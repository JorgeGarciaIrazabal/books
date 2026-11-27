# Production Brief — *The Three Paths* (*Beyond the Waterfall*, Book 1)

- **Edition:** Illustrated First Edition (blended-text 7 × 9 in storybook PDF, reflowable EPUB 3, and 720 × 1080 JPEG cover).
- **Word count:** 6,885 words across 9 chapters (`manuscript/001`..`009`), 0 em/en/double dashes.
- **Build script:** `production/build_edition.py` (ReportLab + Pillow via `uv run --with reportlab --with pillow`).
- **Art pipeline:** 4 Codex (`gpt-6.2-sol`) `image_gen` calls total (3 × 2x2 interior sheets yielding 12 cropped scene illustrations `ill-0001.png`..`ill-0012.png`, plus 1 dedicated 2:3 portrait `cover-art.png`, anchored by 3 reference sheets in `assets/references/`). Zero quota fallback needed.
- **Current local exports:**
  - `exports/cover.jpg`: `366,474` bytes, SHA-256 `9aa0d07f2480da08e47b68007a0d673354cc13f37b18cd70f81c41a61ba22cf3` (720 × 1080 JPEG)
  - `exports/the-three-paths.pdf`: `9,001,418` bytes, SHA-256 `4f0d6ae7c6048986ac81c395f0286c0474e157c9bc82bf28575786a2d7091a8f` (47 pages, 7 × 9 in blended-text storybook trim)
  - `exports/the-three-paths.epub`: `2,493,693` bytes, SHA-256 `440a1a7bf020de23dc07b3b05930bee240f24eda7c13d84ed2c46bc674d55704` (reflowable EPUB 3 with 12 embedded illustrations, cover, and full alt text)
- **Visual proof coverage:** Rendered all 47 PDF pages at 110 dpi via `pdftoppm`; visually inspected `exports/cover.jpg`, Title Page, TOC, Ch 1 opener, and all 12 blended-text illustrated pages (rebuilt and re-inspected after fixing the seamless upper sky feathering, footer badge legibility, and Ch 8 `ill-0010` text clearance). Validated EPUB XML well-formedness and all 12 interior `alt` attributes.
- **Rights & release status:** Local reading copy ready for author and Clara's review; public release (`publications/`, `site/`, Git push) held pending explicit author authorization.
