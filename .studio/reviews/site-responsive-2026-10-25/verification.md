# Responsive catalog and reader, 2026-10-25

Status: implemented, verified, and authorized for publication by the author in
the same session ("finish and publish the new version"). Source snapshot:
working tree based on `1e342f0`, with only the site and documentation changes
listed in `handoff.md`.

## Scope

Redesign the public catalog (`site/index.html`) and browser reader
(`site/reader.html`) for phone, tablet, and desktop, with explicit attention to
space, type size, and which controls belong in each format. No manuscript,
publication artifact, manifest, build tool, or vendor library was changed.

## Implemented

- **Catalog:** one compact card per book on phones (cover plate plus details);
  two columns on tablets; three columns on desktop with a `76rem` maximum.
  Search moved first on small screens; language chips, results status,
  download actions, and a visible empty state with a one-tap reset.
- **Reader:** compact header; icon pager on phones; contents drawer with a
  close button; persistent contents rail on wide desktops; "Start over" moved
  into the contents panel; 44px touch targets; safe-area insets; `100dvh`;
  loading state; reading-progress bar.
- **Fixed layout:** the reader measures the rendered page body and sizes the
  frame to the book's own aspect ratio, then calls `rendition.resize()`.
  Pages are no longer clipped or left-anchored in a wide white panel.
- **Reflowable:** reading measure capped at `46rem`; text-size controls remain
  per book in `localStorage`; progress falls back to spine index plus the
  current page within the section when EPUB.js has not generated location
  percentages.
- **Accessibility:** skip link preserved; focus-visible rings (warm gold on
  dark bars); 44×44px interactive targets; 16px search text to prevent iOS
  zoom; `prefers-reduced-motion`; semantic empty-state reset.

## Measured before/after

Measured with headless Chrome (Playwright 1.61.1) against the local build,
using emulated viewports. Card sizes are the first catalog card in CSS pixels.

| Check | Before | After |
| --- | --- | --- |
| Catalog card, 390×844 | 350×862 | 358×298 |
| Catalog card, 320×640 | 280×898 | 288×303 |
| Catalog card, 1440×900 | 330×986 | 367×659 |
| Reader header, reflowable 390×844 | 153px | 106px |
| Reader header, fixed 390×844 | 104px | 56px |
| Pager, 390×844 | 79px | 62px |
| Fixed frame, 1440×900 | 1411×739, page left-anchored/clipped | 589×746, full page at 720:912 |
| Fixed frame, 390×844 | 374×646, page clipped | 380×482, full page at 720:912 |
| Reflowable frame, 1440×900 | 1411×739 | 736×746 |

No horizontal overflow and no JavaScript page errors were observed at
320×640, 390×844, 844×390, 768×1024, 1280×800, or 1440×900 in the final audit.

## Functional checks (all passed)

- Language filter, search, empty state, clear reset, and `/` search shortcut.
- Reflowable: persistent contents, 736px measure, chapter jump, Next-page
  position change, progress 13.3% at chapter 1, text size 120% saved and
  reapplied after reload, bounds at 90%/170%, saved position restored after
  reload, Start over resets position and progress.
- Fixed layout: 589×746 desktop page at 0.789 ratio, chapter jump to page 6 of
  30, illustration loaded (1536×1024 source), 380×482 phone page, page turn,
  contents drawer with six chapters.
- Phone contents drawer: 336px panel, 44px close target, 44px items and Start
  over target, opens and closes without page errors.
- 320px reader: 320px document width, 106px header, 310px frame.

## Automated checks

- `python3 -m unittest discover -s tests`: **51 tests passed**.
- `python3 tools/build_catalog.py build`: manifest, package, hash, and link
  checks passed.
- `node --check` on `catalog.js` and `reader.js`: passed.

## Coverage limits

The browser checks used headless Chrome with emulated mobile/tablet viewports,
not physical phones or tablets, and not every browser. The reader's embedded
EPUB content was exercised through the actual EPUB.js rendering, but this is
not a new literary review or a proof of every page of every book. Screenshots
are curated JPEG evidence, not an exhaustive capture set.

## Evidence

- `metrics.json`: machine-readable before/after measurements and functional
  checks.
- `screenshots/`: before/after catalog and reader views, contents drawer,
  fixed-layout page, chapter page, and empty state.
- `browser-audit.mjs`: the six-viewport capture script.
- `functional-checks.mjs`: the interaction and assertion script.

## Live deployment

- Commit `f045b63` was pushed to `origin/main`.
- GitHub Pages run [40258816097](https://github.com/JorgeGarciaIrazabal/books/actions/runs/40258816097)
  succeeded for both build and deploy.
- Live checks against `https://jorgegarciairazabal.github.io/books/` confirmed
  the new CSS and reader JavaScript are served, all nine EPUB/PDF/cover HEAD
  requests returned 200, the phone catalog card rendered at 358×298 with a
  106px reflowable reader header, the desktop catalog rendered three cards in
  one row at 659px, and the Nell fixed-layout frame rendered at 589×746 at its
  0.789 ratio with a working page turn. No JavaScript page errors were observed.
- Machine-readable result: `live-verification.json`. Live screenshots are in
  `screenshots/live-*.jpg`.
