# Adaptive reader for fixed-layout books, 2026-10-25

Status: implemented and verified locally. Publication is pending author approval;
nothing in this change has been committed or pushed. Source snapshot: the clean
`a135b26` tree plus the site, documentation, task, handoff, and review changes
listed in `handoff.md`.

## Why this change

The fixed-layout edition of *Nell and the Pocket-Sized Storm* is a 720×912 page.
On a 390px phone the reader fitted it to width at 380×482: body text rendered at
about 11.8px, with 244px of the 726px reading area left empty above and below the
page. The page was complete but hard to read, and the layout forced the whole
page into one screen.

The site already reflows the Mila editions through EPUB.js. This change adds the
same reading principle to fixed-layout books without discarding the illustrated
page view.

## What changed

- **A real text view for fixed-layout books.** The reader reads the book's own 30
  page documents through the EPUB.js archive it already has in memory. It keeps
  the real text, chapter headings, illustration order, and alt text; it does not
  invent a summary or a second copy of the book.
- **Continuous, screen-adaptive scrolling.** All 30 pages flow in one scroll,
  separated by page rules and page numbers. The text uses the available width,
  not a fixed canvas. Status follows the page at the top of the viewport, and
  the progress bar follows the scroll position.
- **Text size that works in both modes.** The A−/A+ controls now appear for
  fixed-layout books when the text view is active. The base is 19px on phones
  and tablets and 18px on desktop; the range is 90–170% (up to 32.3px on a
  phone). The size is saved per book. The illustrated page view keeps its
  original typography.
- **A page/text toggle.** A `Text` / `Pages` button appears in the reader header
  for fixed-layout books. The choice is saved per book. Switching preserves the
  current section: page 2 in the text view returns to page 2 in the page view,
  and back.
- **Sensible defaults.** Text view is the default on phones, small phones, phone
  landscape, tablet landscape, and short landscape laptops up to 1399×820. The
  full illustrated page remains the default on tablet portrait and on a 1440px
  desktop, where it fits well. The toggle is available everywhere.
- **Illustrations that do not cause layout jumps.** All 12 illustrations load
  lazily from the EPUB archive when they approach the viewport. Their intended
  aspect ratios are reserved before the image arrives. The alt text is preserved.
- **Small-header fix.** At 320px the new Pages button initially wrapped the
  header to three rows (155px, leaving 422px to read). The title now flexes to
  the remaining width; the header is two rows (106px) and the reading area is
  472px.
- **Reflowable defaults.** The Mila editions now start at 115% on phones (18.4px
  from a 16px base), 110% on tablets (17.6px), and 100% on desktop (16px). The
  existing 90–170% controls and per-book saved preference still apply.
- **The illustrated page view is unchanged.** Fixed pages still fit their native
  720:912 ratio and the page-turn controls still work. The change adds a reading
  mode; it does not replace the book's layout.

## Default and measured sizes

| Device / viewport | Default | Reading area | Body text |
| --- | --- | --- | --- |
| Phone 390×844 | text | 390×676 | 19px |
| Small phone 320×640 | text | 320×472 | 19px |
| Phone landscape 844×390 | text | 800×280 | 19px |
| Tablet portrait 768×1024 | page | 700×886 (720:912) | about 21.8px on the page |
| Tablet landscape 1024×768 | text | 800×624 | 19px |
| Laptop 1280×800 / 1366×768 | text | 800×650 / 800×616 | 18px |
| Desktop 1440×900 | page | 589×746 (720:912) | about 18.3px on the page |
| Desktop 1440×900, text selected | text | 736×746, 672px measure | 18px |

The earlier fixed-page phone baseline was 380×482 with 11.8px text and 244px of
unused vertical space. The adaptive view fills the 676px height and uses the full
390px width. At 320px the corrected header leaves 472px of reading height instead
of 422px.

## Functional verification

All of the following passed in the final audit:

- Phone opens Nell in the text view with all 30 pages, 12 illustrations, and no
  horizontal overflow.
- Scrolling to each illustrated page loads all 12 images from the EPUB archive;
  natural sizes and alt text were recorded in `metrics.json`.
- The status changes to the page at the top of the viewport; the progress bar
  follows the scroll.
- A+ grows body text from 19px to 20.9px and saves the 110% preference.
- Switching to Pages shows the current page (page 2) at the 720:912 ratio; Next
  goes to page 3 and Previous returns to page 2.
- Switching back to Text returns to page 2.
- Contents jumps to *2. A Very Thirsty Cloud*, page 6, with the chapter heading
  visible.
- Start over returns to the top, clears progress to 0%, and reload keeps the
  text view and the reset position.
- Tablet portrait keeps the full illustrated page by default and switches to
  text at the current page.
- Desktop keeps the page view by default; the text view is capped at 736px with
  a 672px reading measure and returns to page 1 when toggled back.
- Reflowable Mila starts at 18.4px, grows to 20px at 125%, and restores both the
  size and the saved page after reload. The Spanish edition starts at 18.4px with
  no text toggle and no overflow.
- At 320px and 170% text the body is 32.3px, the header is two rows (106px), and
  there is no horizontal overflow. PageDown scrolls the focused text view.
- Catalog language filters, empty state, and one-tap reset still work.

## Automated checks

- `python3 -m unittest discover -s tests`: 51 tests passed.
- `python3 tools/build_catalog.py build`: manifest, package, hash, and link
  checks passed.
- `node --check site/assets/js/reader.js` and `site/assets/js/catalog.js`:
  passed.
- Playwright audit: eight viewports (320×640, 390×844, 844×390, 768×1024,
  1024×768, 1280×800, 1366×768, 1440×900), three books, both reader modes,
  catalog states, all 12 illustrations, and no JavaScript page or console errors.
- Every tested viewport reported zero horizontal overflow.

## Coverage limits

- The browser checks used headless Chrome with emulated mobile and tablet
  viewports, not physical devices, and not every browser.
- This is a reader-layout review, not a new literary review and not a proof of
  every page of every book. The book text and illustrations were preserved from
  the published EPUB; no manuscript or publication artifact changed.
- The text view is an additional reading mode. The illustrated page view remains
  available and is still the default where it fits well.
- Text extraction targets the studio's fixed-layout structure (`.story`
  paragraphs, `.chapter-heading`, and `figure img`). A fixed-layout EPUB with a
  different internal structure would need an adapter before this view could be
  relied on for that book.
- No accessibility certification is claimed. The checks cover focusability,
  labels, touch-target sizes, keyboard scrolling, text growth to 170%, and
  reduced-motion handling; they do not replace a screen-reader audit on real
  devices.

## Evidence

- `metrics.json`: before/after measurements, viewport matrix, functional checks,
  all 12 image checks, accessibility checks, and console/page errors.
- `screenshots/`: phone text view and illustrated page view, small phone,
  phone landscape, Mila, tablet page and text, tablet landscape, laptop text,
  desktop page and text, and the catalog at phone/tablet/desktop.
- `browser-audit.mjs`: reproducible viewport and interaction audit.
- `accessibility-checks.mjs`: 320px maximum text, labels, and keyboard check.
