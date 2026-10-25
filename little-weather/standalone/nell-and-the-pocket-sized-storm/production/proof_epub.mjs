// Render actual, extracted EPUB XHTML with embedded fonts and compare all 30
// compositions to the approved HTML. Chrome is a proof renderer, not an e-reader.
import {spawn} from 'node:child_process';
import {readFile, writeFile, mkdir, mkdtemp, rm} from 'node:fs/promises';
import {join} from 'node:path';
import {tmpdir} from 'node:os';
import {pathToFileURL} from 'node:url';

const [chromePath, extracted, approvedPath, output] = process.argv.slice(2);
if (!output) throw Error('Usage: node proof_epub.mjs CHROME EXTRACTED APPROVED_HTML OUTPUT');
const profile = await mkdtemp(join(tmpdir(), 'nell-epub-chrome-'));
const chrome = spawn(chromePath, ['--headless=new', '--no-sandbox', '--disable-gpu',
  '--disable-dev-shm-usage', '--allow-file-access-from-files', '--remote-debugging-pipe',
  `--user-data-dir=${profile}`, 'about:blank'], {stdio:['ignore','ignore','pipe','pipe','pipe']});
let serial=0, pending=new Map(), listeners=[], buffer=Buffer.alloc(0), stderr='';
chrome.stderr.on('data', chunk=>{stderr=(stderr+chunk).slice(-5000);});
chrome.stdio[4].on('data', chunk=>{
  buffer=Buffer.concat([buffer,chunk]);
  let index;
  while((index=buffer.indexOf(0))>=0){
    const raw=buffer.subarray(0,index).toString();buffer=buffer.subarray(index+1);
    if(!raw) continue;
    const message=JSON.parse(raw);
    if(message.id){const item=pending.get(message.id);if(item){clearTimeout(item.timer);pending.delete(message.id);message.error?item.reject(Error(JSON.stringify(message.error))):item.resolve(message.result);}}
    else {for(const listener of [...listeners])if(listener.method===message.method&&listener.sessionId===message.sessionId){listeners=listeners.filter(x=>x!==listener);clearTimeout(listener.timer);listener.resolve(message.params);}}
  }
});
function send(method,params={},sessionId){return new Promise((resolve,reject)=>{
  const id=++serial,timer=setTimeout(()=>{pending.delete(id);reject(Error(`CDP timeout: ${method}\n${stderr}`));},30000);
  pending.set(id,{resolve,reject,timer});chrome.stdio[3].write(JSON.stringify({id,method,params,...(sessionId?{sessionId}:{})})+'\0');
});}
function event(method,sessionId){return new Promise((resolve,reject)=>{
  const item={method,sessionId,resolve,timer:setTimeout(()=>{listeners=listeners.filter(x=>x!==item);reject(Error(`Event timeout: ${method}`));},30000)};listeners.push(item);
});}
const expression=`(async()=>{
 await document.fonts.ready;
 await Promise.all([...document.images].map(i=>i.decode()));
 const box=(n,b)=>{const r=n.getBoundingClientRect();return {x:r.x-b.x,y:r.y-b.y,width:r.width,height:r.height};};
 return [...document.querySelectorAll('.page')].map(page=>{
  const b=page.getBoundingClientRect();
  return {page:Number(page.id.match(/(\\d+)$/)[1]),width:b.width,height:b.height,
    font:getComputedStyle(page.querySelector('.story')).fontSize,
    fonts_loaded:document.fonts.check('22.4px "Noto Serif"')&&document.fonts.check('12px "Noto Sans"'),
    paragraphs:[...page.querySelectorAll('.story p')].map(p=>({text:p.textContent,...box(p,b)})),
    headings:[...page.querySelectorAll('h1,.chapter-heading')].map(n=>({text:n.textContent,...box(n,b)})),
    image:page.querySelector('img')?{...box(page.querySelector('img'),b),decoded:page.querySelector('img').complete,
      native:[page.querySelector('img').naturalWidth,page.querySelector('img').naturalHeight],alt:page.querySelector('img').alt}:null,
    folio:box(page.querySelector('footer'),b)};
 });
})()`;
let result;
try {
  await mkdir(join(output,'renders'),{recursive:true});
  const {targetId}=await send('Target.createTarget',{url:'about:blank'});
  const {sessionId}=await send('Target.attachToTarget',{targetId,flatten:true});
  await send('Page.enable',{},sessionId);
  await send('Emulation.setDeviceMetricsOverride',{width:720,height:912,deviceScaleFactor:1,mobile:false},sessionId);
  async function navigate(path){
    const loaded=event('Page.loadEventFired',sessionId);
    await send('Page.navigate',{url:pathToFileURL(path).href},sessionId);await loaded;
    const evaluated=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},sessionId);
    if(evaluated.exceptionDetails)throw Error(JSON.stringify(evaluated.exceptionDetails));
    return evaluated.result.value;
  }
  const original=await navigate(approvedPath);
  if(original.length!==30)throw Error('Approved HTML does not have 30 pages');
  const actual=[],failures=[];
  for(let page=1;page<=30;page++){
    const padded=String(page).padStart(3,'0');
    const records=await navigate(join(extracted,'EPUB','pages',`page-${padded}.xhtml`));
    if(records.length!==1||records[0].page!==page)throw Error(`Wrong page document: ${page}`);
    const current=records[0],reference=original[page-1];actual.push(current);
    const issues=[];
    if(current.width!==720||current.height!==912||current.font!=='22.4px'||!current.fonts_loaded)issues.push('viewport/font');
    function compare(a,b,path){
      if(typeof a==='number'&&typeof b==='number'){if(Math.abs(a-b)>.15)issues.push(`${path}: ${a} versus ${b}`);}
      else if(Array.isArray(a)&&Array.isArray(b)){if(a.length!==b.length)issues.push(`${path}: count`);else a.forEach((v,i)=>compare(v,b[i],`${path}[${i}]`));}
      else if(a&&b&&typeof a==='object'&&typeof b==='object'){for(const key of Object.keys(a))compare(a[key],b[key],path+'.'+key);}
      else if(a!==b)issues.push(`${path}: value`);
    }
    compare(current.paragraphs,reference.paragraphs,'paragraphs');
    compare(current.headings,reference.headings,'headings');
    compare(current.image,reference.image,'image');
    compare(current.folio,reference.folio,'folio');
    if(issues.length)failures.push({page,issues});
    const shot=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,
      clip:{x:0,y:0,width:720,height:912,scale:1}},sessionId);
    await writeFile(join(output,'renders',`page-${padded}.png`),Buffer.from(shot.data,'base64'));
  }
  result={renderer:'Chrome DevTools Protocol; actual archive-extracted XHTML, no test script injected into EPUB',
    viewport:[720,912],all_30_text_art_heading_folio_geometries_match_approved_html:failures.length===0,
    tolerance_css_px:.15,failures,measurements:actual,
    limit:'Browser rendering proof; not an installed e-reader application or device test.'};
  await writeFile(join(output,'browser-proof.json'),JSON.stringify(result,null,2)+'\n');
  console.log(`Rendered 30 actual EPUB pages; geometry differences: ${failures.length}.`);
} finally {
  try{await send('Browser.close');}catch{}
  chrome.kill();await rm(profile,{recursive:true,force:true,maxRetries:5,retryDelay:100});
}
if(result?.failures.length)throw Error(JSON.stringify(result.failures));
