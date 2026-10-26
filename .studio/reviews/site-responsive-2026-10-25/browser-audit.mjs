import { mkdir } from 'node:fs/promises';
const { chromium } = await import('/home/jgarcairaza/code/micro-apps/node_modules/playwright/index.mjs');

const BASE = process.env.BASE_URL || 'http://127.0.0.1:8123/';
const OUT = process.env.OUT || '/tmp/opencode/baseline';
const LABEL = process.env.LABEL || 'baseline';
await mkdir(OUT, { recursive: true });

const sizes = [
  { name: 'phone', width: 390, height: 844, deviceScaleFactor: 3, isMobile: true, hasTouch: true },
  { name: 'phone-small', width: 320, height: 640, deviceScaleFactor: 2, isMobile: true, hasTouch: true },
  { name: 'phone-landscape', width: 844, height: 390, deviceScaleFactor: 2, isMobile: true, hasTouch: true },
  { name: 'tablet', width: 768, height: 1024, deviceScaleFactor: 2, isMobile: true, hasTouch: true },
  { name: 'laptop', width: 1280, height: 800, deviceScaleFactor: 1 },
  { name: 'desktop', width: 1440, height: 900, deviceScaleFactor: 1 }
];

const books = ['nell-and-the-pocket-sized-storm', 'mila-and-the-missing-moon', 'mila-y-la-luna-perdida'];
const report = { label: LABEL, base: BASE, renderer: null, pages: {} };

const browser = await chromium.launch({
  executablePath: '/usr/bin/google-chrome',
  headless: true,
  args: ['--no-sandbox', '--disable-dev-shm-usage']
});
report.renderer = browser.version();

async function metrics(page) {
  return page.evaluate(() => {
    const rect = (sel) => {
      const el = document.querySelector(sel);
      if (!el) return null;
      const r = el.getBoundingClientRect();
      const s = getComputedStyle(el);
      return {
        w: Math.round(r.width), h: Math.round(r.height),
        top: Math.round(r.top), left: Math.round(r.left),
        fontSize: s.fontSize, lineHeight: s.lineHeight, display: s.display,
        position: s.position, overflowY: s.overflowY, visibility: s.visibility,
        transform: s.transform === 'none' ? 'none' : 'set'
      };
    };
    const cards = [...document.querySelectorAll('.book')].map(el => {
      const r = el.getBoundingClientRect();
      return { w: Math.round(r.width), h: Math.round(r.height), top: Math.round(r.top), left: Math.round(r.left) };
    });
    const rows = new Set(cards.map(c => c.top)).size;
    const smallTargets = [...document.querySelectorAll('button, a, input')].filter(el => {
      const r = el.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) return false;
      return r.height < 44 || r.width < 44;
    }).map(el => {
      const r = el.getBoundingClientRect();
      return { tag: el.tagName, text: (el.textContent || el.getAttribute('aria-label') || '').trim().slice(0, 40), w: Math.round(r.width), h: Math.round(r.height) };
    });
    return {
      viewport: { w: innerWidth, h: innerHeight },
      scrollWidth: document.documentElement.scrollWidth,
      bodyScrollHeight: document.body.scrollHeight,
      horizontalOverflow: document.documentElement.scrollWidth > innerWidth + 1,
      h1: rect('h1'),
      tagline: rect('.tagline'),
      controls: rect('.controls'),
      search: rect('#search'),
      summary: rect('.summary'),
      bookTitle: rect('.book-title'),
      btn: rect('.btn'),
      chip: rect('.chip'),
      badge: rect('.badge'),
      footer: rect('.site-footer'),
      cards,
      cardRows: rows,
      smallTargets
    };
  });
}

async function readerMetrics(page) {
  return page.evaluate(() => {
    const rect = (sel) => {
      const el = document.querySelector(sel);
      if (!el) return null;
      const r = el.getBoundingClientRect();
      const s = getComputedStyle(el);
      return {
        w: Math.round(r.width), h: Math.round(r.height),
        top: Math.round(r.top), left: Math.round(r.left),
        fontSize: s.fontSize, display: s.display, visibility: s.visibility,
        transform: s.transform === 'none' ? 'none' : 'set', position: s.position
      };
    };
    const smallTargets = [...document.querySelectorAll('button, a')].filter(el => {
      const r = el.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) return false;
      return r.height < 44 || r.width < 44;
    }).map(el => {
      const r = el.getBoundingClientRect();
      return { text: (el.textContent || el.getAttribute('aria-label') || '').trim().slice(0, 40), w: Math.round(r.width), h: Math.round(r.height) };
    });
    return {
      viewport: { w: innerWidth, h: innerHeight },
      scrollWidth: document.documentElement.scrollWidth,
      horizontalOverflow: document.documentElement.scrollWidth > innerWidth + 1,
      bar: rect('.reader-bar'),
      title: rect('.reader-title'),
      tocToggle: rect('#toc-toggle'),
      fontBox: rect('#font-controls'),
      stage: rect('.reader-stage'),
      frame: rect('.epub-frame'),
      pager: rect('.pager-bar'),
      status: rect('#reader-status'),
      prev: rect('#prev'),
      next: rect('#next'),
      toc: rect('#toc-panel'),
      tocVisible: (() => { const el = document.querySelector('#toc-panel'); return el ? getComputedStyle(el).visibility : null; })(),
      smallTargets
    };
  });
}

for (const size of sizes) {
  const context = await browser.newContext({
    viewport: { width: size.width, height: size.height },
    deviceScaleFactor: size.deviceScaleFactor,
    isMobile: Boolean(size.isMobile),
    hasTouch: Boolean(size.hasTouch)
  });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.goto(BASE, { waitUntil: 'networkidle' });
  await page.evaluate(async () => {
    const step = Math.round(innerHeight * 0.8);
    for (let y = 0; y < document.body.scrollHeight; y += step) {
      window.scrollTo(0, y);
      await new Promise(r => setTimeout(r, 60));
    }
    window.scrollTo(0, 0);
  });
  await page.waitForTimeout(300);
  await page.screenshot({ path: `${OUT}/${LABEL}-catalog-${size.name}.png`, fullPage: true });
  const cat = await metrics(page);
  cat.errors = errors.slice();

  report.pages[`catalog-${size.name}`] = cat;

  for (const id of books) {
    const p = await context.newPage();
    const errs = [];
    p.on('pageerror', e => errs.push(e.message));
    await p.goto(`${BASE}reader.html?book=${id}`, { waitUntil: 'domcontentloaded' });
    try {
      await p.waitForFunction(() => /Reading:|Page \d|Back at/.test(document.querySelector('#reader-status')?.textContent || ''), null, { timeout: 60000 });
      await p.locator('#epub-frame iframe').first().waitFor({ timeout: 20000 });
      await p.waitForTimeout(400);
    } catch (e) {
      errs.push('reader wait failed: ' + e.message);
    }
    await p.screenshot({ path: `${OUT}/${LABEL}-reader-${id}-${size.name}.png` });
    const m = await readerMetrics(p);
    m.errors = errs;
    m.status = await p.locator('#reader-status').innerText().catch(() => '');
    report.pages[`reader-${id}-${size.name}`] = m;
    await p.close();
  }
  await context.close();
}

await browser.close();
console.log(JSON.stringify(report, null, 2));
