import { mkdir } from 'node:fs/promises';
import assert from 'node:assert/strict';
const { chromium } = await import('/home/jgarcairaza/code/micro-apps/node_modules/playwright/index.mjs');

const BASE = 'http://127.0.0.1:8123/';
const OUT = '/tmp/opencode/final/checks';
await mkdir(OUT, { recursive: true });

const browser = await chromium.launch({
  executablePath: '/usr/bin/google-chrome',
  headless: true,
  args: ['--no-sandbox', '--disable-dev-shm-usage']
});

const report = { renderer: browser.version(), checks: [], shots: [], errors: [] };

function watch(page, label) {
  page.on('pageerror', e => report.errors.push(`${label}: ${e.message}`));
  page.on('console', m => { if (m.type() === 'error') report.errors.push(`${label} console: ${m.text()}`); });
}

async function readerReady(page) {
  await page.waitForFunction(() => /Reading:|Page \d|Back at/.test(document.querySelector('#reader-status')?.textContent || ''), null, { timeout: 90000 });
  await page.locator('#epub-frame iframe').first().waitFor({ timeout: 30000 });
  await page.waitForTimeout(500);
}

async function position(page, id) {
  return page.evaluate(id => JSON.parse(localStorage.getItem('reader-position:' + id) || 'null')?.cfi, id);
}

async function waitPositionChange(page, id, previous) {
  await page.waitForFunction(({ id, previous }) => {
    const cfi = JSON.parse(localStorage.getItem('reader-position:' + id) || 'null')?.cfi;
    return Boolean(cfi) && cfi !== previous;
  }, { id, previous }, { timeout: 20000 });
}

// ---------- catalog ----------
{
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, deviceScaleFactor: 2 });
  const page = await ctx.newPage(); watch(page, 'catalog');
  await page.goto(BASE, { waitUntil: 'networkidle' });
  await page.getByRole('button', { name: 'Español', exact: true }).click();
  assert.equal(await page.locator('.book:visible').count(), 1);
  await page.getByRole('button', { name: 'English', exact: true }).click();
  assert.equal(await page.locator('.book:visible').count(), 2);
  await page.getByRole('button', { name: 'All languages', exact: true }).click();
  await page.locator('#search').fill('no-such-book-xyz');
  await page.waitForFunction(() => !document.querySelector('#empty-state').hidden);
  assert.equal(await page.locator('.book:visible').count(), 0);
  assert.match(await page.locator('#results-status').innerText(), /No books match/);
  assert.equal(await page.locator('#clear-filters').isVisible(), true);
  await page.locator('#clear-filters').click();
  await page.waitForFunction(() => document.querySelector('#empty-state').hidden);
  assert.equal(await page.locator('.book:visible').count(), 3);
  assert.equal(await page.locator('#search').inputValue(), '');
  await page.locator('body').click({ position: { x: 5, y: 5 } });
  await page.keyboard.press('/');
  assert.equal(await page.evaluate(() => document.activeElement?.id), 'search');
  report.checks.push('Catalog: language filter, search, empty state, clear reset, and / shortcut all behave');
  await ctx.close();
}

// ---------- reflowable: desktop ----------
const reflow = 'mila-and-the-missing-moon';
{
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
  const page = await ctx.newPage(); watch(page, 'reflow-desktop');
  await page.goto(`${BASE}reader.html?book=${reflow}`, { waitUntil: 'domcontentloaded' });
  await readerReady(page);

  assert.equal(await page.locator('#toc-panel').isVisible(), true);
  assert.equal(await page.locator('#toc-toggle').isVisible(), false);
  const frame = await page.locator('#epub-frame').boundingBox();
  assert.ok(frame.width <= 737 && frame.width >= 735, `reflow frame width ${frame.width}`);
  assert.equal(await page.locator('.toc-list button').count(), 14);
  assert.equal(await page.locator('#font-controls').isVisible(), true);
  assert.equal(await page.locator('#start-over').isVisible(), true);

  const before = await position(page, reflow);
  await page.getByRole('button', { name: '1. The Empty Table', exact: true }).click();
  await waitPositionChange(page, reflow, before);
  await page.waitForFunction(() => /Reading: 1\. The Empty Table/.test(document.querySelector('#reader-status')?.textContent || ''));
  const progress1 = await page.locator('#progress-fill').evaluate(el => el.style.width);
  assert.ok(parseFloat(progress1) > 0, `progress should advance, got ${progress1}`);
  await page.screenshot({ path: `${OUT}/reflow-chapter-desktop.png` });
  report.checks.push(`Reflowable desktop: persistent contents, ${frame.width}px measure, chapter jump, progress ${progress1}`);

  const chapterPos = await position(page, reflow);
  await page.locator('#next').click();
  await waitPositionChange(page, reflow, chapterPos);
  report.checks.push('Reflowable desktop: Next page advances the saved position');

  const beforeFont = await page.locator('#font-larger').evaluate(el => el.disabled);
  assert.equal(beforeFont, false);
  await page.locator('#font-larger').click();
  await page.locator('#font-larger').click();
  await page.waitForFunction(() => /Text size 120%/.test(document.querySelector('#reader-status')?.textContent || ''));
  const prefs = await page.evaluate(id => JSON.parse(localStorage.getItem('reader-prefs:' + id) || 'null'), reflow);
  assert.equal(prefs.scale, 120);
  await page.reload({ waitUntil: 'domcontentloaded' });
  await readerReady(page);
  const restoredPrefs = await page.evaluate(id => JSON.parse(localStorage.getItem('reader-prefs:' + id) || 'null'), reflow);
  assert.equal(restoredPrefs.scale, 120);
  report.checks.push('Reflowable: text size 120% saved and reapplied after reload');

  await page.locator('#start-over').click();
  await page.waitForFunction(() => /Back at the beginning/.test(document.querySelector('#reader-status')?.textContent || ''));
  const resetProgress = await page.locator('#progress-fill').evaluate(el => el.style.width);
  assert.ok(parseFloat(resetProgress) <= 1, `progress after start over ${resetProgress}`);
  report.checks.push('Reflowable: Start over resets progress and position');

  await page.screenshot({ path: `${OUT}/reflow-restored-desktop.png` });
  await ctx.close();
}

// ---------- reflowable: phone TOC + font row ----------
{
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, deviceScaleFactor: 2 });
  const page = await ctx.newPage(); watch(page, 'reflow-phone');
  await page.goto(`${BASE}reader.html?book=${reflow}`, { waitUntil: 'domcontentloaded' });
  await readerReady(page);

  assert.equal(await page.locator('#toc-panel').isVisible(), false);
  assert.equal(await page.locator('#font-controls').isVisible(), true);
  const fontBox = await page.locator('#font-smaller').boundingBox();
  const backBox = await page.locator('.back-link').boundingBox();
  assert.ok(fontBox.height >= 44 && backBox.height >= 44, 'touch targets');
  await page.locator('#toc-toggle').click();
  await page.waitForFunction(() => getComputedStyle(document.querySelector('#toc-panel')).visibility === 'visible');
  const closeBox = await page.locator('#toc-close').boundingBox();
  assert.ok(closeBox.width >= 44 && closeBox.height >= 44, `close target ${closeBox.width}x${closeBox.height}`);
  assert.equal(await page.locator('#start-over').isVisible(), true);
  await page.screenshot({ path: `${OUT}/reflow-toc-phone.png` });
  await page.locator('#toc-close').click();
  await page.waitForFunction(() => getComputedStyle(document.querySelector('#toc-panel')).visibility === 'hidden');
  report.checks.push('Reflowable phone: compact header, 44px controls, contents drawer opens/closes');

  await page.locator('#toc-toggle').click();
  await page.waitForFunction(() => getComputedStyle(document.querySelector('#toc-panel')).visibility === 'visible');
  await page.locator('#start-over').click();
  await page.waitForFunction(() => /Back at the beginning/.test(document.querySelector('#reader-status')?.textContent || ''));
  await page.waitForFunction(() => getComputedStyle(document.querySelector('#toc-panel')).visibility === 'hidden');
  report.checks.push('Reflowable phone: Start over closes the drawer and resets');
  await ctx.close();
}

// ---------- fixed layout: desktop chapter/page + illustration ----------
const fixed = 'nell-and-the-pocket-sized-storm';
{
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
  const page = await ctx.newPage(); watch(page, 'fixed-desktop');
  await page.goto(`${BASE}reader.html?book=${fixed}`, { waitUntil: 'domcontentloaded' });
  await readerReady(page);

  assert.equal(await page.locator('#toc-panel').isVisible(), true);
  assert.equal(await page.locator('#font-controls').isVisible(), false);
  const frame = await page.locator('#epub-frame').boundingBox();
  const ratio = frame.width / frame.height;
  assert.ok(Math.abs(ratio - 720 / 912) < 0.01, `fixed ratio ${ratio}`);
  assert.equal(await page.locator('.toc-list button').count(), 6);

  const before = await position(page, fixed);
  await page.getByRole('button', { name: '2. A Very Thirsty Cloud', exact: true }).click();
  await waitPositionChange(page, fixed, before);
  await page.waitForFunction(() => /Page \d+ of 30/.test(document.querySelector('#reader-status')?.textContent || ''));
  const chapterStatus = await page.locator('#reader-status').innerText();
  const chapterPage = Number((chapterStatus.match(/Page (\d+) of 30/) || [])[1]);
  assert.ok(chapterPage > 1, `chapter jump page ${chapterPage}`);
  await page.screenshot({ path: `${OUT}/fixed-chapter2-desktop.png` });
  const imgInfo = await page.evaluate(() => {
    const ifr = document.querySelector('#epub-frame iframe');
    const doc = ifr.contentDocument;
    const imgs = [...doc.images].map(i => ({ w: i.naturalWidth, h: i.naturalHeight, complete: i.complete }));
    return { bodyW: doc.body.offsetWidth, bodyH: doc.body.offsetHeight, imgs };
  });
  assert.ok(imgInfo.bodyW > 0 && imgInfo.bodyH > 0);
  report.checks.push(`Fixed desktop: ${Math.round(frame.width)}x${Math.round(frame.height)} page, ratio ${ratio.toFixed(3)}, chapter jump to ${chapterStatus}, images ${JSON.stringify(imgInfo.imgs)}`);
  await ctx.close();
}

// ---------- fixed layout: phone ----------
{
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, deviceScaleFactor: 2 });
  const page = await ctx.newPage(); watch(page, 'fixed-phone');
  await page.goto(`${BASE}reader.html?book=${fixed}`, { waitUntil: 'domcontentloaded' });
  await readerReady(page);
  const frame = await page.locator('#epub-frame').boundingBox();
  assert.ok(frame.width <= 381, `fixed phone frame ${frame.width}`);
  assert.ok(Math.abs(frame.width / frame.height - 720 / 912) < 0.01);
  await page.locator('#next').click();
  await page.waitForFunction(() => /Page 2 of 30/.test(document.querySelector('#reader-status')?.textContent || ''));
  await page.screenshot({ path: `${OUT}/fixed-page2-phone.png` });
  await page.locator('#toc-toggle').click();
  await page.waitForFunction(() => getComputedStyle(document.querySelector('#toc-panel')).visibility === 'visible');
  await page.screenshot({ path: `${OUT}/fixed-toc-phone.png` });
  report.checks.push(`Fixed phone: ${Math.round(frame.width)}x${Math.round(frame.height)} page, page turn, contents drawer`);
  await ctx.close();
}

await browser.close();
await (await import('node:fs/promises')).writeFile('/tmp/opencode/final/checks/report.json', JSON.stringify(report, null, 2));
console.log(JSON.stringify(report, null, 2));
