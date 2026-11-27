import assert from 'node:assert/strict';
const { chromium } = await import('/home/jgarcairaza/code/micro-apps/node_modules/playwright/index.mjs');
const b=await chromium.launch({executablePath:'/usr/bin/google-chrome',headless:true,args:['--no-sandbox']});
const out={checks:[],errors:[]};

// Spanish Mila on a phone
{
  const c=await b.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,deviceScaleFactor:2});
  const p=await c.newPage(); p.on('pageerror',e=>out.errors.push('spanish: '+e.message));
  await p.goto('http://127.0.0.1:8123/reader.html?book=mila-y-la-luna-perdida',{waitUntil:'domcontentloaded'});
  await p.waitForFunction(()=>/Leyendo:|Reading:/.test(document.querySelector('#reader-status')?.textContent||''),null,{timeout:90000});
  await p.waitForTimeout(600);
  const s=await p.evaluate(()=>{
    const ifr=document.querySelector('#epub-frame iframe');
    const el=ifr.contentDocument.querySelector('p:not(.chapter-number)');
    return {status:document.querySelector('#reader-status').textContent,font:getComputedStyle(el).fontSize,title:document.title,toggle:document.querySelector('#view-toggle').hidden,overflow:document.documentElement.scrollWidth-document.documentElement.clientWidth};
  });
  console.log('SPANISH', JSON.stringify(s,null,1));
  assert.match(s.status,/Reading: Portada/);
  assert.equal(s.font,'18.4px');
  assert.equal(s.toggle,true);
  assert.equal(s.overflow,0);
  out.checks.push('Spanish Mila: 18.4px default, no text toggle, no overflow');
  await c.close();
}

// 320px max font, keyboard, ARIA
{
  const c=await b.newContext({viewport:{width:320,height:640},isMobile:true,hasTouch:true,deviceScaleFactor:2});
  const p=await c.newPage(); p.on('pageerror',e=>out.errors.push('small: '+e.message));
  await p.goto('http://127.0.0.1:8123/reader.html?book=nell-and-the-pocket-sized-storm',{waitUntil:'domcontentloaded'});
  await p.waitForFunction(()=>document.body.classList.contains('text-mode'),null,{timeout:120000});
  await p.waitForTimeout(700);
  for(let i=0;i<10;i++){ if(await p.locator('#font-larger').isDisabled()) break; await p.locator('#font-larger').click(); }
  const max=await p.evaluate(()=>{
    const tv=document.querySelector('#text-view');
    const p=tv.querySelector('.text-story p');
    const toggle=document.querySelector('#view-toggle');
    return {
      font:getComputedStyle(p).fontSize,
      overflow:document.documentElement.scrollWidth-document.documentElement.clientWidth,
      bar:Math.round(document.querySelector('.reader-bar').getBoundingClientRect().height),
      tv:{w:Math.round(tv.getBoundingClientRect().width),h:Math.round(tv.getBoundingClientRect().height)},
      toggle:{label:toggle.textContent,pressed:toggle.getAttribute('aria-pressed'),aria:toggle.getAttribute('aria-label')},
      textAria:tv.getAttribute('aria-label'),
      tabindex:tv.getAttribute('tabindex'),
      pageAria:tv.querySelector('.text-page')?.getAttribute('aria-label'),
      nextAria:document.querySelector('#next').getAttribute('aria-label')
    };
  });
  console.log('MAX FONT 320', JSON.stringify(max,null,1));
  assert.equal(max.font,'32.3px');
  assert.equal(max.overflow,0);
  assert.equal(max.bar,106);
  assert.equal(max.toggle.pressed,'true');
  assert.equal(max.textAria,'Book text');
  assert.equal(max.tabindex,'0');
  assert.equal(max.pageAria,'Page 1 of 30');
  assert.equal(max.nextAria,'Scroll forward');
  out.checks.push('320px at 170% text: 32.3px, two-row header, no horizontal overflow');

  await p.locator('#text-view').focus();
  const before=await p.evaluate(()=>({scroll:document.querySelector('#text-view').scrollTop,active:document.activeElement?.id||document.activeElement?.tagName}));
  await p.keyboard.press('PageDown');
  await p.waitForTimeout(1200);
  const after=await p.evaluate(()=>({scroll:document.querySelector('#text-view').scrollTop,active:document.activeElement?.id||document.activeElement?.tagName}));
  console.log('KEYBOARD', JSON.stringify({before,after},null,1));
  assert.ok(after.scroll>before.scroll, 'PageDown scroll');
  out.checks.push('Keyboard PageDown scrolls the focused text view');
  await c.close();
}

await b.close();
console.log(JSON.stringify(out,null,2));
