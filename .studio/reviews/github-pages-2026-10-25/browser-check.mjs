// Independent coordinator QA. Requires an installed Playwright module and Chrome.
// PLAYWRIGHT_MODULE may be an absolute path to playwright/index.mjs.
// BASE_URL defaults to the local preview served under the real /books/ subpath.
import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const base = process.env.BASE_URL || 'http://127.0.0.1:8765/books/';
const output = process.env.QA_OUTPUT || '/tmp/books-pages-glm/qa';
await mkdir(output, { recursive: true });
const browser = await chromium.launch({
  executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome',
  headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage']
});
const report = { base, renderer: browser.version(), checks: [], errors: [] };
const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
const page = await context.newPage();
page.on('pageerror', error => report.errors.push(error.message));
const status = () => page.locator('#reader-status').innerText();
async function ready(target = page) {
  await target.waitForFunction(() => /Reading:|Page \d/.test(document.querySelector('#reader-status')?.textContent || ''), null, { timeout: 45000 });
  await target.locator('#epub-frame iframe').waitFor();
}
async function position(id) {
  return page.evaluate(id => JSON.parse(localStorage.getItem('reader-position:' + id) || 'null')?.cfi, id);
}
async function waitPositionChange(id, previous) {
  await page.waitForFunction(({ id, previous }) => {
    const cfi = JSON.parse(localStorage.getItem('reader-position:' + id) || 'null')?.cfi;
    return Boolean(cfi) && cfi !== previous;
  }, { id, previous });
}
try {
  await page.goto(base);
  assert.equal(await page.locator('.book:visible').count(), 3);
  await page.getByRole('button', { name: 'Español', exact: true }).click();
  assert.equal(await page.locator('.book:visible').count(), 1);
  await page.getByRole('button', { name: 'English', exact: true }).click();
  assert.equal(await page.locator('.book:visible').count(), 2);
  await page.getByRole('button', { name: 'All languages', exact: true }).click();
  await page.locator('#search').fill('Nell');
  await page.waitForFunction(() => [...document.querySelectorAll('.book')].filter(e => !e.hidden).length === 1);
  assert.equal(await page.locator('.book:visible').count(), 1);
  await page.locator('#search').fill('no-such-title-1234');
  await page.waitForFunction(() => [...document.querySelectorAll('.book')].every(e => e.hidden));
  assert.equal(await page.locator('.book:visible').count(), 0);
  await page.locator('#search').fill('');
  await page.waitForFunction(() => [...document.querySelectorAll('.book')].every(e => !e.hidden));
  await page.screenshot({ path: output + '/catalog-desktop.png', fullPage: true });
  report.checks.push('Catalog: actual visible cards match language/search filters, including empty results');

  const catalogResponse = await context.request.get(new URL('catalog.json', base).href);
  const catalog = await catalogResponse.json();
  const downloads = [];
  for (const book of catalog.books) {
    for (const [kind, path] of Object.entries(book.downloads)) {
      const response = await context.request.get(new URL(path, base).href);
      assert.equal(response.status(), 200);
      const bytes = await response.body();
      assert.equal(bytes.length, book.sizes[kind]);
      downloads.push({ id: book.id, kind, bytes: bytes.length, sha256: createHash('sha256').update(bytes).digest('hex') });
    }
  }
  report.downloads = downloads;
  report.checks.push('All six HTTP downloads return 200, match declared sizes, and have recorded SHA256 hashes');

  for (const book of catalog.books) {
    const id = book.id;
    await page.goto(new URL('reader.html?book=' + id, base).href);
    await ready();
    assert.equal(await page.locator('#book-title').innerText(), book.title);
    assert.equal(await page.locator('#font-controls').isVisible(), book.layout !== 'fixed');
    assert.equal(await page.locator('#toc-list button').count(), book.layout === 'fixed' ? 6 : 14);
    const first = await position(id);
    await page.locator('#next').click();
    await waitPositionChange(id, first);
    const next = await position(id);
    await page.locator('#prev').click();
    await waitPositionChange(id, next);
    await page.locator('#toc-toggle').click();
    await page.locator('#toc-list button').nth(book.layout === 'fixed' ? 1 : 2).click();
    await page.waitForFunction(() => /2\.|Page 6/.test(document.querySelector('#reader-status').textContent));
    const saved = await position(id);
    await page.reload();
    await ready();
    assert.equal(await position(id), saved);
    if (book.layout === 'fixed') {
      const content = page.frames()[1];
      await content.waitForFunction(() => [...document.images].length > 0 && [...document.images].every(i => i.complete && i.naturalWidth > 0));
      assert.match(await content.locator('body').innerText(), /red kite/);
      await page.screenshot({ path: output + '/nell-desktop.png' });
    } else {
      const before = await page.frames()[1].evaluate(() => parseFloat(getComputedStyle(document.body).fontSize));
      await page.locator('#font-larger').click();
      await page.frames()[1].waitForFunction(before => parseFloat(getComputedStyle(document.body).fontSize) > before, before);
    }
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    report.checks.push(id + ': real EPUB text, contents, next/previous, chapter jump, saved-location reload, and layout-specific controls');
  }

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(base);
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
  await page.screenshot({ path: output + '/catalog-mobile.png', fullPage: true });
  for (const id of ['mila-y-la-luna-perdida', 'nell-and-the-pocket-sized-storm']) {
    await page.goto(new URL('reader.html?book=' + id, base).href);
    await ready();
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    const rect = await page.locator('#next').boundingBox();
    assert.ok(rect.x >= 0 && rect.x + rect.width <= 390 && rect.y + rect.height <= 845);
    await page.screenshot({ path: output + '/mobile-' + id + '.png' });
  }
  report.checks.push('390×844 catalog and Spanish/fixed-layout readers: no horizontal overflow; paging controls remain on screen');

  for (const selection of ['', '?book=unknown-title', '?book=..%2Foutside']) {
    await page.goto(new URL('reader.html' + selection, base).href);
    await page.waitForFunction(() => document.querySelector('#reader-status').classList.contains('is-error'));
    assert.equal(page.frames().length, 1);
  }
  report.checks.push('Missing, unknown, and invalid book selection produce errors without opening an EPUB');

  const privateContext = await browser.newContext();
  await privateContext.addInitScript(() => {
    Object.defineProperty(window, 'localStorage', { get() { throw new DOMException('Storage unavailable', 'SecurityError'); } });
  });
  const privatePage = await privateContext.newPage();
  privatePage.on('pageerror', error => report.errors.push(error.message));
  await privatePage.goto(new URL('reader.html?book=mila-and-the-missing-moon', base).href);
  await ready(privatePage);
  await privateContext.close();
  report.checks.push('EPUB still opens when browser storage is unavailable');
  assert.deepEqual(report.errors, []);
  report.result = 'pass';
} catch (error) {
  report.result = 'fail';
  report.failure = error.stack;
  process.exitCode = 1;
} finally {
  await browser.close();
  await writeFile(output + '/browser-results.json', JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report, null, 2));
}
