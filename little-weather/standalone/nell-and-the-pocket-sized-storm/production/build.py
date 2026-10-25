#!/usr/bin/env python3
"""Build the declared 30-page illustrated reading edition with local Chrome.

This produces a proof candidate; hashes and checks do not confer art acceptance.
"""
from __future__ import annotations

import base64
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile

from PIL import Image

BOOK = Path(__file__).resolve().parents[1]
EXPORTS = BOOK / "exports"
STEM = "nell-and-the-pocket-sized-storm"
BODY_PT = 16.8
PAGE_IN = (7.5, 9.5)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local_path(relative: str) -> Path:
    path = (BOOK / relative).resolve()
    if not path.is_relative_to(BOOK.resolve()):
        raise ValueError(f"Input escapes book root: {relative}")
    if not path.is_file():
        raise ValueError(f"Missing input: {relative}")
    return path


def read_pages(manifest: dict) -> list[dict]:
    """Parse each declared chapter separately, never a glob or joined heading stream."""
    if len(set(manifest["chapters"])) != len(manifest["chapters"]):
        raise ValueError("Duplicate chapter paths")
    details = {item["path"]: item for item in manifest["chapter_details"]}
    pages = []
    for chapter_number, relative in enumerate(manifest["chapters"], 1):
        source = local_path(relative).read_text(encoding="utf-8")
        chapter = details[relative]
        chunks = re.split(r"^## Page (\d+)\s*$", source, flags=re.MULTILINE)
        if len(chunks) < 3:
            raise ValueError(f"No page sections in {relative}")
        for i in range(1, len(chunks), 2):
            number, text = int(chunks[i]), chunks[i + 1].strip()
            if not text or re.search(r"^#", text, re.MULTILINE):
                raise ValueError(f"Empty page or leaked heading on page {number}")
            if "\u2014" in text:
                raise ValueError(f"House-style em dash on page {number}")
            pages.append({"number": number, "text": text, "chapter": relative,
                          "chapter_number": chapter_number, "chapter_id": chapter["id"],
                          "chapter_title": chapter["title"]})
    expected = list(range(1, manifest["story_pages"] + 1))
    if [p["number"] for p in pages] != expected or len(pages) != 30:
        raise ValueError("Expected exactly 30 consecutive story pages in declared order")
    return pages


def png_dimensions(path: Path) -> tuple[int, int]:
    header = path.read_bytes()[:24]
    if header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError(f"Expected an actual PNG asset: {path}")
    return struct.unpack(">II", header[16:24])


def load_art(plan: dict, manifest: dict, pages: list[dict], design: dict) -> tuple[dict, list[dict]]:
    if plan['chapter_paths'] != manifest['chapters']:
        raise ValueError('Illustration chapter order differs from book.json')
    lookup = {p['number']: p for p in pages}
    layouts = {p['page']: p for p in design['pages']}
    by_page, ids, assets, records = {}, set(), set(), []
    counts = dict.fromkeys(manifest['chapters'], 0)
    for art in plan['illustrations']:
        number = art['page']; entry = layouts[number]
        if art['id'] in ids or art['asset'] in assets or number in by_page:
            raise ValueError('Duplicate illustration ID, asset or page')
        if lookup[number]['chapter'] != art['chapter'] or entry.get('art_id') != art['id']:
            raise ValueError(f'Illustration/layout chapter mismatch: {art["id"]}')
        if number < art['disclosure']['not_before_page'] or not art.get('alt_text', '').strip():
            raise ValueError(f'Invalid disclosure or alternative: {art["id"]}')
        path = local_path(art['asset'])
        width_px, height_px = png_dimensions(path)
        b = entry['art_box']; scale = (max if b['fit']=='cover' else min)(b['width']/width_px, b['height']/height_px)
        width_in, height_in = width_px*scale, height_px*scale
        # PNG is intentional: true alpha edges must survive both browser and PDF.
        with Image.open(path) as original:
            has_alpha = 'A' in original.getbands() or 'transparency' in original.info
            alpha_extrema = original.convert('RGBA').getchannel('A').getextrema()
        crop_fraction = [max(0,1-b['width']/width_in), max(0,1-b['height']/height_in)]
        if max(crop_fraction) > .025:
            raise ValueError(f'Background crop exceeds declared minimal allowance: {art["id"]}')
        if 'vignette' in entry['type'] and (not has_alpha or alpha_extrema[0] == 255):
            raise ValueError(f'Vignette requires actual transparency: {art["id"]}')
        by_page[number] = {**art, 'data_uri':'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode(),
                           'width_in':width_in, 'height_in':height_in}
        records.append({'id':art['id'],'chapter':art['chapter'],'page':number,'asset':art['asset'],
            'sha256':sha256(path),'placement_derivative':art['asset'],'placement_derivative_sha256':sha256(path),
            'derivative_encoding':'Original PNG; dimensions and alpha preserved','native_pixels':[width_px,height_px],
            'placed_inches':[round(width_in,6),round(height_in,6)],'placement_box_inches':b,
            'effective_ppi':[round(width_px/width_in,2),round(height_px/height_in,2)],
            'fit':b['fit'],'crop':b['crop'],'crop_fraction_of_native_axes':crop_fraction,'crop_anchor':'center','alpha_preserved':has_alpha,'alpha_extrema':list(alpha_extrema),
            'intentional_background':bool(entry.get('background')),'alt_text':art['alt_text'],
            'plan_status_at_build':art['status']})
        ids.add(art['id']); assets.add(art['asset']); counts[art['chapter']] += 1
    if len(records) != 12 or any(not plan['art_per_chapter']['min'] <= c <= plan['art_per_chapter']['max'] for c in counts.values()):
        raise ValueError(f'Expected twelve illustrations, two per chapter: {counts}')
    return by_page, records


def positioned(box: dict, height: bool = False) -> str:
    result = f'left:{box["x"]}in;top:{box["y"]}in;width:{box["width"]}in;'
    if height: result += f'height:{box["height"]}in;'
    return result


def compose(manifest: dict, pages: list[dict], art_by_page: dict, design: dict) -> str:
    articles = []
    for page, entry in zip(pages, design['pages']):
        number = page['number']; art = art_by_page.get(number)
        parts = re.split(r'\n\s*\n', page['text'])
        contents = []
        if art:
            contents.append(f'<figure data-illustration="{art["id"]}" data-background="{str(bool(entry.get("background"))).lower()}" style="{positioned(entry["art_box"],True)}"><img src="{art["data_uri"]}" alt="{html.escape(art["alt_text"],quote=True)}" style="width:{art["width_in"]:.8f}in;height:{art["height_in"]:.8f}in"></figure>')
        if number == 1:
            contents.append(f'<h1 style="{positioned(entry["title_box"])}">{html.escape(manifest["title"])}</h1>')
        if entry['chapter_title']:
            cb = entry['chapter_box']
            contents.append(f'<div class="chapter-heading" style="{positioned(cb)}"><span class="chapter-number">Chapter {page["chapter_number"]}</span><h2>{html.escape(page["chapter_title"])}</h2></div>')
        for b in entry['text_blocks']:
            start, end = b.get('paragraphs',[0,None])
            text = ''.join(f'<p data-paragraph="{i}">{html.escape(p.replace(chr(10)," "))}</p>' for i,p in enumerate(parts) if i >= start and (end is None or i < end))
            contents.append(f'<div class="story" style="{positioned(b)}line-height:{entry["leading"]};--paragraph-gap:{entry["paragraph_gap_in"]}in">{text}</div>')
        quiet = html.escape(json.dumps(entry.get('quiet_zone')),quote=True)
        articles.append(f'<article class="page" data-layout="{entry["type"]}" data-quiet-zone="{quiet}" id="page-{number}" aria-label="Page {number}">{"".join(contents)}<footer class="folio {"recto" if number%2 else "verso"}">{number}</footer></article>')
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'''+html.escape(manifest['title'])+'''</title><style>
@page{size:7.5in 9.5in;margin:0}*{box-sizing:border-box}html,body{margin:0;padding:0}
body{background:#dce5e8;color:#233b45;font-family:"Noto Serif","DejaVu Serif",serif}
.page{position:relative;width:7.5in;height:9.5in;margin:22px auto;background:#fffdf7;break-after:page;page-break-after:always;box-shadow:0 5px 30px #1e344222;overflow:hidden}
.page:last-child{break-after:auto;page-break-after:auto}.story,h1,.chapter-heading{position:absolute;z-index:2}
.story{font-size:16.8pt}p{margin:0 0 var(--paragraph-gap);orphans:2;widows:2}p:last-child{margin-bottom:0}
h1{margin:0;font-size:30pt;line-height:1.12;letter-spacing:-.45px;color:#254e60}
.chapter-number{display:block;font-family:"Noto Sans",sans-serif;font-size:9pt;letter-spacing:1.2px;text-transform:uppercase;color:#607d84;margin-bottom:.09in}
h2{font-size:22pt;line-height:1.15;font-weight:600;margin:0;color:#254e60}
figure{position:absolute;margin:0;display:flex;align-items:center;justify-content:center;z-index:1;overflow:hidden}figure img{display:block;object-fit:contain;max-width:none}
.folio{position:absolute;top:9.23in;font-size:8pt;line-height:1;font-family:"Noto Sans",sans-serif;color:#607d84;z-index:3}.folio.recto{right:.4in}.folio.verso{left:.4in}.page:has(figure[data-background="true"]) .folio{background:#fffdf7e6;border-radius:3px;padding:2px 4px;top:9.20in}
@media print{html,body{background:#fffdf7;print-color-adjust:exact;-webkit-print-color-adjust:exact}.page{margin:0;box-shadow:none}}
</style></head><body>'''+ '\n'.join(articles)+'''
<script id="layout-report" type="application/json">{}</script><script>
function checkLayout(){
 const failures=[]; const rounded=n=>Math.round(n*100)/100;
 const box=(r,b)=>({x:rounded(r.left-b.left),y:rounded(r.top-b.top),width:rounded(r.width),height:rounded(r.height)});
 const intersects=(a,b)=>a.left<b.right-.1&&a.right>b.left+.1&&a.top<b.bottom-.1&&a.bottom>b.top+.1;
 const measurements=[...document.querySelectorAll('.page')].map(page=>{
  const bounds=page.getBoundingClientRect(), errors=[]; const picture=page.querySelector('img');
  const ib=picture?picture.getBoundingClientRect():null;
  const footer=page.querySelector('footer').getBoundingClientRect();
  const paras=[...page.querySelectorAll('p')]; const texts=[...page.querySelectorAll('p,h1,.chapter-heading')];
  let canvas,ctx;if(picture){canvas=document.createElement('canvas');canvas.width=picture.naturalWidth;canvas.height=picture.naturalHeight;ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.drawImage(picture,0,0);}
  const background=picture&&picture.parentElement.dataset.background==='true';
  const quiet=JSON.parse(page.dataset.quietZone);
  let closest=99999; const overlaps=[];
  for(const node of texts){const r=node.getBoundingClientRect();closest=Math.min(closest,footer.top-r.bottom);
   if(r.left<bounds.left-.2||r.right>bounds.right+.2||r.top<bounds.top-.2||r.bottom>footer.top-7)errors.push('text outside reading area');
   if(background&&node.matches('p')&&quiet){const q={left:bounds.left+quiet.x*96,top:bounds.top+quiet.y*96,right:bounds.left+(quiet.x+quiet.width)*96,bottom:bounds.top+(quiet.y+quiet.height)*96};if(r.left<q.left-.2||r.right>q.right+.2||r.top<q.top-.2||r.bottom>q.bottom+.2)errors.push('text leaves commissioned quiet zone');}
   if(ib&&intersects(r,ib)&&!background){
    const x=Math.max(0,Math.floor((Math.max(r.left,ib.left)-ib.left)*canvas.width/ib.width));
    const y=Math.max(0,Math.floor((Math.max(r.top,ib.top)-ib.top)*canvas.height/ib.height));
    const w=Math.min(canvas.width-x,Math.ceil((Math.min(r.right,ib.right)-ib.left)*canvas.width/ib.width)-x);
    const h=Math.min(canvas.height-y,Math.ceil((Math.min(r.bottom,ib.bottom)-ib.top)*canvas.height/ib.height)-y);
    if(w>0&&h>0){const px=ctx.getImageData(x,y,w,h).data;let opaque=0;for(let k=3;k<px.length;k+=4)if(px[k]>40)opaque++;if(opaque){errors.push('opaque art/text collision');overlaps.push({paragraph:node.dataset.paragraph||'heading',opaque_pixels:opaque});}}
   }
  }
  for(let a=0;a<texts.length;a++)for(let b=a+1;b<texts.length;b++)if(intersects(texts[a].getBoundingClientRect(),texts[b].getBoundingClientRect()))errors.push('text/text collision');
  if(picture&&(!picture.complete||!picture.naturalWidth))errors.push('image not decoded');
  const visibleBox=background?picture.parentElement.getBoundingClientRect():ib;
  if(visibleBox&&(visibleBox.left<bounds.left-.2||visibleBox.right>bounds.right+.2||visibleBox.top<bounds.top-.2||visibleBox.bottom>bounds.bottom+.2))errors.push('image outside page');
  if(page.scrollWidth>page.clientWidth||page.scrollHeight>page.clientHeight)errors.push('page overflow');
  if(errors.length)failures.push({page:page.id,errors:[...new Set(errors)],overlaps});
  return {page:Number(page.id.slice(5)),layout:page.dataset.layout,body_font_px:getComputedStyle(page.querySelector('.story')).fontSize,footer_clearance_px:rounded(closest),paragraphs:paras.map(p=>({index:Number(p.dataset.paragraph),...box(p.getBoundingClientRect(),bounds)})),chapter_title:!!page.querySelector('h2'),image:picture?{id:picture.parentElement.dataset.illustration,decoded:picture.complete&&picture.naturalWidth>0,natural_pixels:[picture.naturalWidth,picture.naturalHeight],rendered_pixels:[rounded(ib.width),rounded(ib.height)],box:box(ib,bounds),intentional_background:background,alt:picture.alt}:null};
 });
 const report={pages:measurements.length,image_count:document.images.length,failures,measurements};document.querySelector('#layout-report').textContent=JSON.stringify(report);document.body.dataset.layout=failures.length?'failed':'passed';
}
if(document.readyState==='complete')checkLayout();else window.addEventListener('load',checkLayout,{once:true});
</script></body></html>'''


def main() -> None:
    manifest_path=BOOK/'book.json'; manifest=json.loads(manifest_path.read_text())
    plan_path=local_path(manifest['illustration_plan']); plan=json.loads(plan_path.read_text())
    layout_path=local_path('production/layout-v3.json'); design=json.loads(layout_path.read_text())
    if [p['page'] for p in design['pages']] != list(range(1,31)):
        raise ValueError('Design must explicitly describe every story page in order')
    if design['body_type_points'] != BODY_PT or design['running_headers']:
        raise ValueError('Unexpected body size or running headers')
    pages=read_pages(manifest); by_page,art_records=load_art(plan,manifest,pages,design)
    EXPORTS.mkdir(exist_ok=True); html_path=EXPORTS/f'{STEM}.html'; pdf_path=EXPORTS/f'{STEM}.pdf'
    html_path.write_text(compose(manifest,pages,by_page,design))
    chrome=shutil.which('google-chrome') or shutil.which('chromium')
    if not chrome: raise RuntimeError('Local Chrome or Chromium is required')
    with tempfile.TemporaryDirectory(prefix='nell-illustrated-chrome-') as profile:
        command=[chrome,'--headless=new','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--window-size=900,1200',f'--user-data-dir={profile}','--no-pdf-header-footer','--run-all-compositor-stages-before-draw','--virtual-time-budget=5000',f'--print-to-pdf={pdf_path}','--dump-dom',html_path.as_uri()]
        result=subprocess.run(command,text=True,capture_output=True,timeout=90)
        if result.returncode: raise RuntimeError(result.stderr[-3000:])
        match=re.search(r'<script id="layout-report" type="application/json">(.*?)</script>',result.stdout,re.DOTALL)
        if not match: raise RuntimeError('Browser did not return layout report')
        layout=json.loads(html.unescape(match.group(1)))
        (EXPORTS/'illustrated-layout-check.json').write_text(json.dumps(layout,indent=2)+'\n')
        if layout.get('pages') != 30 or layout.get('image_count') != 12 or layout.get('failures'):
            raise RuntimeError(f'Layout validation failed: {layout.get("failures",layout)}')
    info=subprocess.run(['pdfinfo',str(pdf_path)],text=True,capture_output=True,check=True).stdout
    if not re.search(r'^Pages:\s+30$',info,re.MULTILINE): raise RuntimeError('Actual PDF must contain exactly30 pages')
    inputs=[manifest_path,plan_path,layout_path,Path(__file__),BOOK/'production/verify_illustrated.py',*[local_path(p) for p in manifest['chapters']],*[local_path(a['asset']) for a in plan['illustrations']]]
    for relative in ['production/visual-style.md','production/art-direction.md','assets/references/cast-reference-v1.png']:
        if (BOOK/relative).is_file(): inputs.append(BOOK/relative)
    for item in plan['illustrations']:
        provenance=item.get('provenance',{})
        if provenance.get('prompt_record'):inputs.append(local_path(provenance['prompt_record']))
        for reference in provenance.get('reference_assets',[]):
            relative=reference if isinstance(reference,str) else reference.get('path')
            if relative:inputs.append(local_path(relative))
    hashes={str(p.relative_to(BOOK)):sha256(p) for p in [*dict.fromkeys(inputs),html_path,pdf_path,EXPORTS/'illustrated-layout-check.json']}
    record={'schema_version':3,'title':manifest['title'],'edition':manifest.get('edition'),'purpose':'private digital reading proof candidate','story_pages':30,'pdf_pages':30,'page_size_inches':list(PAGE_IN),'chapter_order':manifest['chapters'],'body_type_points':BODY_PT,'body_leading':'page-specific; see production/layout-v3.json','paragraph_gap_inches':'page-specific; see layout','illustration_count':len(art_records),'illustrations':art_records,'layout_source':'production/layout-v3.json','layout_overflow':[],'browser_layout_report':'exports/illustrated-layout-check.json','sha256':hashes,'build':'python3 production/build.py','renderer':subprocess.run([chrome,'--version'],capture_output=True,text=True,check=True).stdout.strip(),'accessibility':'Meaningful alternatives are embedded in self-contained HTML. PDF tag and alt preservation require separate verification.','review_limit':'Mechanical geometry and fidelity checks do not certify visual or narrative approval.'}
    (EXPORTS/'reading-edition-manifest.json').write_text(json.dumps(record,indent=2)+'\n')
    print(f'Built {pdf_path}\n30 pages;12 illustrations;16.8pt body;PNG alpha preserved;no detected opaque art/text collision.')


if __name__ == '__main__':
    main()
