import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
const { chromium } = await import('/home/jgarcairaza/code/micro-apps/node_modules/playwright/index.mjs');

const BASE = 'http://127.0.0.1:8123/';
const BOOK = 'nell-and-the-pocket-sized-storm';
const OUT = '/tmp/opencode/narration-qa';
await mkdir(OUT, { recursive: true });

const browser = await chromium.launch({
  executablePath: '/usr/bin/google-chrome',
  headless: true,
  args: ['--no-sandbox', '--disable-dev-shm-usage']
});

const report = { base: BASE, renderer: browser.version(), checks: [], errors: [], requests: [] };

function watch(page, label) {
  page.on('pageerror', error => report.errors.push(`${label}: ${error.message}`));
  page.on('console', message => {
    if (message.type() === 'error') { report.errors.push(`${label} console: ${message.text()}`); }
  });
  page.on('request', request => {
    if (request.url().includes('/narration/') && request.url().endsWith('.mp3')) {
      report.requests.push(request.url().split('/narration/')[1]);
    }
  });
}

function check(name, condition, detail) {
  report.checks.push({ name, pass: Boolean(condition), detail: detail || '' });
  assert.ok(condition, `${name}: ${detail || ''}`);
}

// A deterministic Audio double: the reader can be driven without waiting for real audio.
const audioMock = () => {
  window.__audios = [];
  window.Audio = class MockAudio {
    constructor() {
      this.listeners = {};
      this._src = '';
      this.paused = true;
      this.currentTime = 0;
      this.preload = '';
      window.__audios.push(this);
    }
    get src() { return this._src; }
    set src(value) { this._src = value; }
    addEventListener(type, fn) { (this.listeners[type] = this.listeners[type] || []).push(fn); }
    play() {
      if (window.__failAudio) {
        const error = new Error('blocked');
        error.name = 'NotAllowedError';
        return Promise.reject(error);
      }
      this.paused = false;
      return Promise.resolve();
    }
    pause() { this.paused = true; }
    removeAttribute() { this._src = ''; }
    emit(type) { (this.listeners[type] || []).forEach(fn => fn()); }
  };
};

// 1. Narration control appears, never autoplays, and follows the current page.
{
  const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const page = await context.newPage();
  watch(page, 'phone');
  await page.addInitScript(audioMock);
  await page.goto(`${BASE}reader.html?book=${BOOK}`);
  await page.waitForSelector('#narration-bar:not([hidden])', { timeout: 30000 });
  const label = await page.textContent('#listen-label');
  check('listen control visible', label.trim() === 'Listen', label);
  check('no audio requested before click', report.requests.length === 0, JSON.stringify(report.requests));

  await page.click('#listen-toggle');
  await page.waitForTimeout(400);
  const pressed = await page.getAttribute('#listen-toggle', 'aria-pressed');
  check('pressed state after play', pressed === 'true', pressed);
  const srcs = await page.evaluate(() => window.__audios.map(a => a.src));
  check('first page audio requested', srcs.some(src => src.endsWith('/page-01.mp3')), JSON.stringify(srcs));

  // Phone starts in the adaptive text view; the page being read is marked.
  await page.waitForSelector('.text-page.is-narrating', { timeout: 15000 });
  const marked = await page.$$eval('.text-page.is-narrating', nodes => nodes.map(n => n.id));
  check('text view marks narrated page', marked.length === 1, JSON.stringify(marked));

  await page.screenshot({ path: `${OUT}/phone-text-narration.png`, fullPage: false });

  // Pause stops the audio and keeps the reading position.
  await page.click('#listen-toggle');
  await page.waitForTimeout(200);
  const paused = await page.getAttribute('#listen-toggle', 'aria-pressed');
  check('pause clears pressed state', paused === 'false', paused);
  await context.close();
}

// 1b. Page mode: a page turn follows the narration and a track end advances the page.
{
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  watch(page, 'page-mode');
  await page.addInitScript(audioMock);
  await page.goto(`${BASE}reader.html?book=${BOOK}`);
  await page.waitForSelector('#narration-bar:not([hidden])', { timeout: 30000 });
  await page.waitForTimeout(600);
  await page.click('#listen-toggle');
  await page.waitForTimeout(400);
  await page.click('#next');
  await page.waitForTimeout(900);
  const afterTurn = await page.evaluate(() => window.__audios.map(a => a.src));
  check('page turn follows narration', afterTurn.some(src => src.endsWith('/page-02.mp3')), JSON.stringify(afterTurn));
  const atTwo = (await page.textContent('#reader-status')).trim();
  check('page view moved to page 2', /Page 2 of 30/.test(atTwo), atTwo);

  const active = await page.evaluate(() => {
    const audio = window.__audios.find(item => !item.paused);
    if (audio) { audio.emit('ended'); }
    return Boolean(audio);
  });
  check('audio element active before end', active, 'no active audio');
  await page.waitForTimeout(1200);
  const status = (await page.textContent('#reader-status')).trim();
  check('narrated end turns the page', /Page 3 of 30/.test(status), status);

  // Switching to the text view with narration on marks the page being read.
  await page.click('#view-toggle');
  await page.waitForSelector('.text-page.is-narrating', { timeout: 15000 });
  const marked = await page.$$eval('.text-page.is-narrating', nodes => nodes.map(node => node.id));
  check('desktop text view marks narrated page', marked.length === 1, JSON.stringify(marked));
  await page.screenshot({ path: `${OUT}/desktop-page-narration.png`, fullPage: false });
  await context.close();
}

// 2. Missing audio degrades to silent reading.
{
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const page = await context.newPage();
  watch(page, 'missing');
  await page.addInitScript(() => { window.__failAudio = true; });
  await page.addInitScript(audioMock);
  await page.route('**/narration/**/page-0*.mp3', route => route.fulfill({ status: 404, body: '' }));
  await page.goto(`${BASE}reader.html?book=${BOOK}`);
  await page.waitForSelector('#narration-bar:not([hidden])', { timeout: 30000 });
  await page.waitForFunction(() => /Page \d+ of 30/.test(document.getElementById('reader-status').textContent), null, { timeout: 30000 });
  await page.click('#listen-toggle');
  await page.waitForTimeout(700);
  const status = (await page.textContent('#reader-status')).trim();
  const pressed = await page.getAttribute('#listen-toggle', 'aria-pressed');
  check('missing audio reports and stops', pressed === 'false' && /could not start|narration/i.test(status), `${pressed} | ${status}`);
  const nextEnabled = await page.isEnabled('#next');
  check('reading still usable after audio failure', nextEnabled, 'next disabled');
  await context.close();
}

// 3. Desktop layout and no horizontal overflow with the narration bar.
{
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  watch(page, 'desktop');
  await page.addInitScript(audioMock);
  await page.goto(`${BASE}reader.html?book=${BOOK}`);
  await page.waitForSelector('#narration-bar:not([hidden])', { timeout: 30000 });
  await page.waitForFunction(() => /Page \d+ of 30/.test(document.getElementById('reader-status').textContent), null, { timeout: 30000 });
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  check('no horizontal overflow on desktop', overflow <= 0, String(overflow));
  const status = (await page.textContent('#reader-status')).trim();
  check('desktop opens in page view', /Page 1 of 30/.test(status), status);
  await page.screenshot({ path: `${OUT}/desktop-narration.png`, fullPage: false });
  await context.close();
}

// 4. Real audio: the browser actually requests and starts page 1.
{
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  const mp3 = [];
  page.on('request', request => {
    if (request.url().endsWith('.mp3')) { mp3.push(request.url().split('/').pop()); }
  });
  page.on('pageerror', error => report.errors.push(`real-audio: ${error.message}`));
  await page.goto(`${BASE}reader.html?book=${BOOK}`);
  await page.waitForSelector('#narration-bar:not([hidden])', { timeout: 30000 });
  await page.waitForFunction(() => /Page \d+ of 30/.test(document.getElementById('reader-status').textContent), null, { timeout: 30000 });
  await page.click('#listen-toggle');
  await page.waitForTimeout(2500);
  const pressed = await page.getAttribute('#listen-toggle', 'aria-pressed');
  check('real browser starts page 1 audio', mp3.includes('page-01.mp3') && pressed === 'true',
        `${JSON.stringify(mp3)} | pressed=${pressed}`);
  await page.click('#listen-toggle');
  report.mp3 = mp3;
  await context.close();
}

// 5. A book without narration shows no Listen control.
{
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  watch(page, 'no-narration');
  await page.goto(`${BASE}reader.html?book=mila-and-the-missing-moon`);
  await page.waitForTimeout(4000);
  const hidden = await page.evaluate(() => document.getElementById('narration-bar').hidden);
  check('no listen control without narration', hidden, 'bar visible');
  await context.close();
}

await writeFile(`${OUT}/report.json`, JSON.stringify(report, null, 2) + '\n');
await browser.close();
console.log(`checks: ${report.checks.length}, errors: ${report.errors.length}, mocked audio requests: ${report.requests.length}, real mp3: ${JSON.stringify(report.mp3)}`);
if (report.errors.length) { console.log(report.errors.join('\n')); process.exit(1); }
