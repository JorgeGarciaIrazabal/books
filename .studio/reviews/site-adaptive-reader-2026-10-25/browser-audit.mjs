import { mkdir, writeFile } from 'node:fs/promises';
import assert from 'node:assert/strict';
const { chromium } = await import('/home/jgarcairaza/code/micro-apps/node_modules/playwright/index.mjs');

const BASE = 'http://127.0.0.1:8123/';
const OUT = '/tmp/opencode/adaptive';
await mkdir(OUT, { recursive: true });

const browser = await chromium.launch({
  executablePath: '/usr/bin/google-chrome',
  headless: true,
  args: ['--no-sandbox', '--disable-dev-shm-usage']
});

const report = {
  base: BASE,
  renderer: browser.version(),
  viewports: {},
  functional: [],
  image_checks: [],
  errors: []
};

function watch(page, label) {
  page.on('pageerror', e => report.errors.push(`${label}: ${e.message}`));
  page.on('console', m => {
    if (m.type() === 'error' && !/favicon/i.test(m.text())) {
      report.errors.push(`${label} console: ${m.text()}`);
    }
  });
}

async function waitReader(page, label) {
  await page.waitForFunction(() => {
    const body = document.body;
    const frame = document.querySelector('#epub-frame iframe');
    return body.classList.contains('text-mode') || Boolean(frame);
  }, null, { timeout: 120000 });
  await page.waitForFunction(() => /Reading:|Page \d/.test(document.querySelector('#reader-status')?.textContent || ''), null, { timeout: 120000 });
  await page.waitForTimeout(700);
}

async function waitNellText(page) {
  await page.waitForFunction(() => document.body.classList.contains('text-mode'), null, { timeout: 120000 });
  await page.waitForFunction(() => document.querySelectorAll('#text-view .text-page').length === 30, null, { timeout: 120000 });
  await page.waitForTimeout(500);
}

async function waitMila(page) {
  await page.waitForFunction(() => /Reading:/.test(document.querySelector('#reader-status')?.textContent || ''), null, { timeout: 120000 });
  await page.locator('#epub-frame iframe').first().waitFor({ timeout: 30000 });
  await page.waitForTimeout(500);
}

const viewports = [
  { name: 'phone', width: 390, height: 844, mobile: true, dpr: 2 },
  { name: 'phone-small', width: 320, height: 640, mobile: true, dpr: 2 },
  { name: 'phone-landscape', width: 844, height: 390, mobile: true, dpr: 2 },
  { name: 'tablet', width: 768, height: 1024, mobile: true, dpr: 1 },
  { name: 'tablet-landscape', width: 1024, height: 768, mobile: true, dpr: 1 },
  { name: 'laptop', width: 1280, height: 800, mobile: false, dpr: 1 },
  { name: 'laptop-1366', width: 1366, height: 768, mobile: false, dpr: 1 },
  { name: 'desktop', width: 1440, height: 900, mobile: false, dpr: 1 }
];

for (const vp of viewports) {
  const ctx = await browser.newContext({
    viewport: { width: vp.width, height: vp.height },
    isMobile: vp.mobile,
    hasTouch: vp.mobile,
    deviceScaleFactor: vp.dpr
  });
  const entry = {};

  // Catalog
  {
    const page = await ctx.newPage();
    watch(page, `${vp.name}-catalog`);
    await page.goto(BASE, { waitUntil: 'networkidle' });
    entry.catalog = await page.evaluate(() => {
      const cards = [...document.querySelectorAll('.book')];
      return {
        visibleBooks: cards.length,
        firstCard: cards[0] ? { w: Math.round(cards[0].getBoundingClientRect().width), h: Math.round(cards[0].getBoundingClientRect().height) } : null,
        columns: new Set(cards.map(c => Math.round(c.getBoundingClientRect().top))).size,
        overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth
      };
    });
    if (['phone', 'tablet', 'laptop', 'desktop'].includes(vp.name)) {
      await page.screenshot({ path: `${OUT}/${vp.name}-catalog.png`, fullPage: true });
    }
    await page.close();
  }

  // Nell
  {
    const page = await ctx.newPage();
    watch(page, `${vp.name}-nell`);
    await page.goto(BASE + 'reader.html?book=nell-and-the-pocket-sized-storm', { waitUntil: 'domcontentloaded' });
    await waitReader(page, vp.name);
    if (await page.evaluate(() => document.body.classList.contains('text-mode'))) {
      await waitNellText(page);
    }
    entry.nell = await page.evaluate(() => {
      const tv = document.querySelector('#text-view');
      const frame = document.querySelector('#epub-frame');
      const p = tv && !tv.hidden ? tv.querySelector('.text-story p') : null;
      const fr = frame.getBoundingClientRect();
      const tvr = tv.getBoundingClientRect();
      return {
        mode: document.body.classList.contains('text-mode') ? 'text' : 'page',
        header: Math.round(document.querySelector('.reader-bar').getBoundingClientRect().height),
        pager: Math.round(document.querySelector('.pager-bar').getBoundingClientRect().height),
        textBox: tv.hidden ? null : { w: Math.round(tvr.width), h: Math.round(tvr.height) },
        textFont: p ? getComputedStyle(p).fontSize : null,
        pageFrame: getComputedStyle(frame).display === 'none' ? null : { w: Math.round(fr.width), h: Math.round(fr.height), ratio: Number((fr.width / fr.height).toFixed(3)) },
        toggle: document.querySelector('#view-toggle').textContent,
        pages: document.querySelectorAll('#text-view .text-page').length,
        images: document.querySelectorAll('#text-view .text-illustration img').length,
        status: document.querySelector('#reader-status').textContent,
        overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth
      };
    });
    if (['phone', 'phone-small', 'phone-landscape', 'tablet', 'tablet-landscape', 'laptop', 'laptop-1366', 'desktop'].includes(vp.name)) {
      await page.screenshot({ path: `${OUT}/${vp.name}-nell-${entry.nell.mode}.png`, fullPage: false });
    }
    await page.close();
  }

  // Mila
  {
    const page = await ctx.newPage();
    watch(page, `${vp.name}-mila`);
    await page.goto(BASE + 'reader.html?book=mila-and-the-missing-moon', { waitUntil: 'domcontentloaded' });
    await waitMila(page);
    entry.mila = await page.evaluate(() => {
      const frame = document.querySelector('#epub-frame').getBoundingClientRect();
      const ifr = document.querySelector('#epub-frame iframe');
      let font = null;
      try {
        const p = ifr.contentDocument.querySelector('p:not(.chapter-number)');
        font = p ? getComputedStyle(p).fontSize : null;
      } catch (e) {}
      return {
        header: Math.round(document.querySelector('.reader-bar').getBoundingClientRect().height),
        frame: { w: Math.round(frame.width), h: Math.round(frame.height) },
        font,
        toggleHidden: document.querySelector('#view-toggle').hidden,
        fontControlsHidden: document.querySelector('#font-controls').hidden,
        status: document.querySelector('#reader-status').textContent,
        overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth
      };
    });
    if (vp.name === 'phone') {
      await page.screenshot({ path: `${OUT}/phone-mila.png`, fullPage: false });
    }
    await page.close();
  }

  report.viewports[vp.name] = entry;
  await ctx.close();
}

// ---------- breakpoint assertions ----------
{
  const v = report.viewports;
  assert.equal(v.phone.nell.mode, 'text');
  assert.equal(v.phone.nell.header, 106);
  assert.equal(v['phone-small'].nell.mode, 'text');
  assert.equal(v['phone-small'].nell.header, 106);
  assert.ok(v['phone-small'].nell.textBox.h > 450, 'phone-small reading height ' + v['phone-small'].nell.textBox.h);
  assert.equal(v['phone-small'].nell.overflow, 0);
  assert.equal(v['phone-landscape'].nell.mode, 'text');
  assert.equal(v['phone-landscape'].nell.overflow, 0);
  assert.equal(v.tablet.nell.mode, 'page');
  assert.equal(v['tablet-landscape'].nell.mode, 'text');
  assert.ok(v['tablet-landscape'].nell.textBox.w >= 800);
  assert.equal(v.laptop.nell.mode, 'text');
  assert.equal(v['laptop-1366'].nell.mode, 'text');
  assert.equal(v.desktop.nell.mode, 'page');
  for (const [name, entry] of Object.entries(v)) {
    assert.equal(entry.catalog.overflow, 0, name + ' catalog overflow');
    assert.equal(entry.nell.overflow, 0, name + ' nell overflow');
    assert.equal(entry.mila.overflow, 0, name + ' mila overflow');
    assert.equal(entry.mila.toggleHidden, true, name + ' mila toggle hidden');
  }
  report.functional.push('Breakpoints: phone/phone-small/phone-landscape/tablet-landscape/laptops use text; tablet portrait and 1440 desktop use the page view; no horizontal overflow at any width');
}

// ---------- phone functional ----------
{
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, deviceScaleFactor: 2 });
  const page = await ctx.newPage();
  watch(page, 'functional-phone');
  await page.goto(BASE + 'reader.html?book=nell-and-the-pocket-sized-storm', { waitUntil: 'domcontentloaded' });
  await waitNellText(page);

  assert.equal(await page.locator('#view-toggle').isVisible(), true);
  assert.equal(await page.evaluate(() => document.querySelectorAll('#text-view .text-page').length), 30);
  report.functional.push('Phone opens Nell directly in the reflowable text view with all 30 pages');

  // Every illustration is present and loads when its page is reached.
  const illustrated = [2, 4, 6, 9, 12, 15, 17, 19, 23, 24, 27, 30];
  for (const n of illustrated) {
    await page.evaluate(n => {
      const tv = document.querySelector('#text-view');
      const el = document.querySelector('#text-page-' + n);
      tv.scrollTop = el.offsetTop;
    }, n);
    await page.waitForFunction(n => {
      const img = document.querySelector('#text-page-' + n + ' .text-illustration img');
      return img && img.complete && img.naturalWidth > 0;
    }, n, { timeout: 20000 });
    const info = await page.evaluate(n => {
      const img = document.querySelector('#text-page-' + n + ' .text-illustration img');
      return { page: n, src: img.getAttribute('src'), natural: [img.naturalWidth, img.naturalHeight], alt: img.alt };
    }, n);
    report.image_checks.push(info);
  }
  report.functional.push(`All ${illustrated.length} illustrations loaded in the text view`);

  // Page-aware status and scroll
  await page.evaluate(() => { document.querySelector('#text-view').scrollTop = document.querySelector('#text-page-2').offsetTop; });
  await page.waitForFunction(() => /Page 2 of 30/.test(document.querySelector('#reader-status').textContent));
  await page.screenshot({ path: `${OUT}/phone-nell-text-page2.png` });
  report.functional.push('Scrolling changes the status to the page at the top of the viewport');

  // Font size
  const fontBefore = await page.evaluate(() => getComputedStyle(document.querySelector('#text-page-2 .text-story p')).fontSize);
  await page.locator('#font-larger').click();
  await page.waitForTimeout(400);
  const fontAfter = await page.evaluate(() => ({
    font: getComputedStyle(document.querySelector('#text-page-2 .text-story p')).fontSize,
    scale: JSON.parse(localStorage.getItem('reader-prefs:nell-and-the-pocket-sized-storm') || 'null')?.scale,
    status: document.querySelector('#reader-status').textContent
  }));
  assert.ok(parseFloat(fontAfter.font) > parseFloat(fontBefore));
  assert.equal(fontAfter.scale, 110);
  report.functional.push(`Text size grows from ${fontBefore} to ${fontAfter.font} and is saved`);

  // Toggle to pages, page turn, and back
  await page.locator('#view-toggle').click();
  await page.waitForFunction(() => !document.body.classList.contains('text-mode'));
  await page.waitForTimeout(900);
  const pageMode = await page.evaluate(() => {
    const frame = document.querySelector('#epub-frame').getBoundingClientRect();
    return {
      ratio: Number((frame.width / frame.height).toFixed(3)),
      status: document.querySelector('#reader-status').textContent,
      toggle: document.querySelector('#view-toggle').textContent,
      fontHidden: document.querySelector('#font-controls').hidden
    };
  });
  assert.ok(Math.abs(pageMode.ratio - 720 / 912) < 0.02);
  assert.match(pageMode.status, /Page 2 of 30/);
  assert.equal(pageMode.toggle, 'Text');
  assert.equal(pageMode.fontHidden, true);
  report.functional.push(`Page view restores the current page at the 720:912 ratio (${pageMode.ratio})`);

  await page.locator('#next').click();
  await page.waitForFunction(() => /Page 3 of 30/.test(document.querySelector('#reader-status').textContent));
  report.functional.push('Page-view Next advances to page 3');
  await page.locator('#prev').click();
  await page.waitForFunction(() => /Page 2 of 30/.test(document.querySelector('#reader-status').textContent));

  await page.locator('#view-toggle').click();
  await page.waitForFunction(() => document.body.classList.contains('text-mode'));
  await page.waitForTimeout(500);
  assert.match(await page.locator('#reader-status').innerText(), /Page 2 of 30/);
  report.functional.push('Returning to text restores page 2');

  // Contents jump
  await page.locator('#toc-toggle').click();
  await page.waitForTimeout(350);
  await page.getByRole('button', { name: '2. A Very Thirsty Cloud', exact: true }).click();
  await page.waitForFunction(() => /Page 6 of 30/.test(document.querySelector('#reader-status').textContent));
  assert.match(await page.locator('#text-page-6 .text-chapter').innerText(), /A Very Thirsty Cloud/);
  report.functional.push('Contents jumps to chapter 2, page 6');

  // Start over
  await page.locator('#toc-toggle').click();
  await page.waitForTimeout(350);
  await page.locator('#start-over').click();
  await page.waitForTimeout(700);
  const reset = await page.evaluate(() => ({
    scroll: document.querySelector('#text-view').scrollTop,
    status: document.querySelector('#reader-status').textContent,
    progress: document.querySelector('#progress-fill').style.width
  }));
  assert.equal(reset.scroll, 0);
  assert.equal(reset.progress, '0%');
  report.functional.push(`Start over returns to the top (${reset.status})`);

  // Reload restores the view and the beginning
  await page.reload({ waitUntil: 'domcontentloaded' });
  await waitNellText(page);
  const reload = await page.evaluate(() => ({
    mode: document.body.classList.contains('text-mode'),
    status: document.querySelector('#reader-status').textContent,
    scroll: document.querySelector('#text-view').scrollTop
  }));
  assert.equal(reload.mode, true);
  assert.equal(reload.scroll, 0);
  report.functional.push('Reload keeps the text view and the reset position');
  await ctx.close();
}

// ---------- tablet portrait functional ----------
{
  const ctx = await browser.newContext({ viewport: { width: 768, height: 1024 }, isMobile: true, hasTouch: true, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  watch(page, 'functional-tablet');
  await page.goto(BASE + 'reader.html?book=nell-and-the-pocket-sized-storm', { waitUntil: 'domcontentloaded' });
  await waitReader(page, 'tablet-functional');
  assert.equal(await page.evaluate(() => document.body.classList.contains('text-mode')), false);
  const ratio = await page.evaluate(() => {
    const f = document.querySelector('#epub-frame').getBoundingClientRect();
    return f.width / f.height;
  });
  assert.ok(Math.abs(ratio - 720 / 912) < 0.02);
  await page.locator('#next').click();
  await page.waitForFunction(() => /Page 2 of 30/.test(document.querySelector('#reader-status').textContent));
  await page.locator('#view-toggle').click();
  await page.waitForFunction(() => document.body.classList.contains('text-mode'));
  await page.waitForTimeout(500);
  assert.match(await page.locator('#reader-status').innerText(), /Page 2 of 30/);
  report.functional.push('Tablet portrait keeps the full page layout by default and switches to text at page 2');
  await ctx.close();
}

// ---------- desktop functional ----------
{
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  watch(page, 'functional-desktop');
  await page.goto(BASE + 'reader.html?book=nell-and-the-pocket-sized-storm', { waitUntil: 'domcontentloaded' });
  await waitReader(page, 'desktop-functional');
  assert.equal(await page.evaluate(() => document.body.classList.contains('text-mode')), false);
  await page.locator('#view-toggle').click();
  await page.waitForFunction(() => document.body.classList.contains('text-mode'));
  await page.waitForTimeout(500);
  const sizes = await page.evaluate(() => {
    const tv = document.querySelector('#text-view').getBoundingClientRect();
    const pageBox = document.querySelector('.text-page').getBoundingClientRect();
    return { tv: Math.round(tv.width), page: Math.round(pageBox.width) };
  });
  assert.equal(sizes.tv, 736);
  assert.equal(sizes.page, 672);
  await page.locator('#view-toggle').click();
  await page.waitForFunction(() => !document.body.classList.contains('text-mode'));
  await page.waitForTimeout(700);
  assert.match(await page.locator('#reader-status').innerText(), /Page 1 of 30/);
  report.functional.push(`Desktop page view is default; text view is capped at ${sizes.tv}px with a ${sizes.page}px reading measure`);
  await ctx.close();
}

// ---------- Mila phone functional ----------
{
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, deviceScaleFactor: 2 });
  const page = await ctx.newPage();
  watch(page, 'functional-mila');
  await page.goto(BASE + 'reader.html?book=mila-and-the-missing-moon', { waitUntil: 'domcontentloaded' });
  await waitMila(page);
  assert.equal(await page.locator('#view-toggle').isHidden(), true);
  assert.equal(await page.locator('#font-controls').isVisible(), true);
  const startFont = await page.evaluate(() => {
    const ifr = document.querySelector('#epub-frame iframe');
    return getComputedStyle(ifr.contentDocument.querySelector('p:not(.chapter-number)')).fontSize;
  });
  assert.equal(startFont, '18.4px');

  await page.locator('#toc-toggle').click();
  await page.waitForTimeout(350);
  await page.getByRole('button', { name: '2. Something White', exact: true }).click();
  await page.waitForFunction(() => /2\. Something White/.test(document.querySelector('#reader-status').textContent));
  await page.locator('#next').click();
  await page.waitForTimeout(500);
  await page.locator('#font-larger').click();
  await page.waitForTimeout(500);
  const larger = await page.evaluate(() => {
    const ifr = document.querySelector('#epub-frame iframe');
    return {
      font: getComputedStyle(ifr.contentDocument.querySelector('p:not(.chapter-number)')).fontSize,
      scale: JSON.parse(localStorage.getItem('reader-prefs:mila-and-the-missing-moon') || 'null')?.scale
    };
  });
  assert.equal(larger.scale, 125);
  assert.equal(larger.font, '20px');
  await page.reload({ waitUntil: 'domcontentloaded' });
  await waitMila(page);
  const restored = await page.evaluate(() => {
    const ifr = document.querySelector('#epub-frame iframe');
    return {
      font: getComputedStyle(ifr.contentDocument.querySelector('p:not(.chapter-number)')).fontSize,
      status: document.querySelector('#reader-status').textContent
    };
  });
  assert.equal(restored.font, '20px');
  assert.match(restored.status, /2\. Something White/);
  report.functional.push(`Reflowable Mila: 18.4px default, 20px at 125%, saved size and page restored (${restored.status})`);
  await ctx.close();
}

// ---------- catalog functional ----------
{
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, deviceScaleFactor: 2 });
  const page = await ctx.newPage();
  watch(page, 'functional-catalog');
  await page.goto(BASE, { waitUntil: 'networkidle' });
  await page.getByRole('button', { name: 'Español', exact: true }).click();
  assert.equal(await page.locator('.book:visible').count(), 1);
  await page.getByRole('button', { name: 'English', exact: true }).click();
  assert.equal(await page.locator('.book:visible').count(), 2);
  await page.getByRole('button', { name: 'All languages', exact: true }).click();
  await page.locator('#search').fill('no-such-book-xyz');
  await page.waitForFunction(() => !document.querySelector('#empty-state').hidden);
  await page.locator('#clear-filters').click();
  await page.waitForFunction(() => document.querySelector('#empty-state').hidden);
  assert.equal(await page.locator('.book:visible').count(), 3);
  report.functional.push('Catalog language filters, empty state, and one-tap reset still work');
  await ctx.close();
}

await browser.close();
await writeFile(`${OUT}/audit.json`, JSON.stringify(report, null, 2));
console.log(JSON.stringify(report, null, 2));
