#!/usr/bin/env python3
"""Build a private reflowable EPUB 3 and render its title page as a catalog cover.

All chapter content comes from book.json order. Requires Chrome and Pillow only
for the rendered title-page JPEG. Does not publish, commit or edit source prose.
Verification evidence is printed as JSON; no unreviewed release is declared.
"""
from pathlib import Path
from html import escape
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import uuid
import xml.etree.ElementTree as ET
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED, ZIP_STORED
from PIL import Image

BOOK = Path(__file__).resolve().parents[1]
OUT = BOOK / 'exports'
XHTML = 'http://www.w3.org/1999/xhtml'
OPF = 'http://www.idpf.org/2007/opf'
EPUB = 'http://www.idpf.org/2007/ops'
CSS = '''html { font-size: 100%; }
body { margin: 5%; font-family: Georgia, "DejaVu Serif", serif; line-height: 1.55; }
p { margin: 0 0 .8em; orphans: 2; widows: 2; }
h1 { font-size: 1.8em; line-height: 1.2; margin: 1em 0; break-after: avoid; }
nav li { margin-bottom: .7em; }
.title-body { margin: 0; background: #eee7d6; color: #302b25; }
.title-page { box-sizing: border-box; min-height: 78vh; padding: 11% 12%;
 text-align: center; display: flex; flex-direction: column; justify-content: center; }
.title-page .series { font-family: sans-serif; font-size: .85em; letter-spacing: .18em;
 text-transform: uppercase; line-height: 1.7; margin: 0 0 4em; }
.title-page h1 { font-weight: normal; font-size: 3.5em; line-height: 1.12; margin: 0; }
.title-page .rule { width: 4em; border: 0; border-top: 1px solid #887047; margin: 3em auto; }
.title-page .number { font-style: italic; font-size: 1.15em; margin-bottom: 4em; }
.title-page .notice { font-family: sans-serif; font-size: .8em; letter-spacing: .03em; }
'''
TAG = re.compile(r'<\|(?:speaker:|im_)|</?(?:whisper|emphasis|soft|fast|slow|stress|forceful)\b|\[(?:sighs|laughs|pause)\]')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def norm(text):
    return ' '.join(text.split())


def document(title, body, body_class=''):
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="{XHTML}" xmlns:epub="{EPUB}" lang="en" xml:lang="en">
<head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{escape(title)}</title><link rel="stylesheet" type="text/css" href="style.css"/></head>
<body class="{body_class}">{body}</body></html>'''


def build():
    meta = json.loads((BOOK/'book.json').read_text(encoding='utf-8'))
    paths = meta['chapters']
    if len(paths) != 22 or len(set(paths)) != len(paths):
        raise ValueError('Expected the 22 distinct declared chapters')
    entries, chapters, sources = {}, [], {}
    for index, relative in enumerate(paths, 1):
        data = (BOOK/relative).read_bytes()
        raw = data.decode('utf-8').strip()
        if TAG.search(raw): raise ValueError(f'Performance tag in {relative}')
        heading, body = raw.split('\n', 1)
        if not heading.startswith('# '): raise ValueError(f'No chapter heading: {relative}')
        title = heading[2:].strip()
        paragraphs = [norm(p) for p in re.split(r'\n\s*\n',body.strip()) if p.strip()]
        if any(re.search(r'^[#*]|<!--', p) for p in paragraphs):
            raise ValueError(f'Unsupported manuscript markup in {relative}')
        filename=f'chapter-{index:02d}.xhtml'
        text='\n'.join('<p>'+escape(p,quote=False)+'</p>' for p in paragraphs)
        entries[filename]=document(title,f'<section epub:type="chapter" role="doc-chapter" id="chapter-{index}"><h1>{escape(title)}</h1>\n{text}</section>')
        chapters.append({'source':relative,'file':filename,'title':title,'paragraphs':paragraphs})
        sources[relative]=sha(data)
    title_body='''<section class="title-page" epub:type="titlepage" aria-labelledby="book-title">
<p class="series">The Goblin Wars</p>
<h1 id="book-title">The Ledger<br/> of Ashes</h1>
<hr class="rule" aria-hidden="true"/>
<p class="number">Book One</p>
<p class="notice">Unofficial fan fiction</p>
</section>'''
    entries['title.xhtml']=document(meta['title'],title_body,'title-body')
    entries['about.xhtml']=document('About this edition','''<section epub:type="copyright-page" role="doc-copyright">
<h1>About this edition</h1>
<p>This is unofficial fan fiction set in the Harry Potter / Wizarding World setting. It is not an official or endorsed publication.</p>
<p>The story follows original characters in an imagined account of the goblin rebellions. Harry Potter and the Wizarding World are properties of their respective rights holders. This free fan work is not authorised, endorsed or sponsored by them, and no official status is claimed.</p>
<p>This reading edition contains twenty-two chapters. Narration, where published, is a separate performance and is not embedded in this book.</p>
</section>''')
    toc=[('title.xhtml','Title'),('about.xhtml','About this edition')]+[(c['file'],c['title']) for c in chapters]
    links='\n'.join(f'<li><a href="{f}">{escape(t)}</a></li>' for f,t in toc)
    entries['nav.xhtml']=document('Contents',f'''<nav epub:type="toc" id="toc" role="doc-toc"><h1>Contents</h1><ol>{links}</ol></nav>
<nav epub:type="landmarks" hidden="hidden"><h2>Landmarks</h2><ol><li><a epub:type="titlepage" href="title.xhtml">Title page</a></li><li><a epub:type="bodymatter" href="chapter-01.xhtml">Begin reading</a></li></ol></nav>''')
    entries['style.css']=CSS
    OUT.mkdir(exist_ok=True)
    cover=OUT/(meta['id']+'-cover.jpg')
    chrome=shutil.which('google-chrome') or shutil.which('chromium')
    if not chrome: raise RuntimeError('Chrome required for exact title-page cover rendering')
    with tempfile.TemporaryDirectory(prefix='ledger-epub-') as temp:
        directory=Path(temp)
        (directory/'title.xhtml').write_text(entries['title.xhtml'],encoding='utf-8')
        (directory/'style.css').write_text(CSS,encoding='utf-8')
        png=directory/'title.png'
        proc=subprocess.run([chrome,'--headless','--no-sandbox','--disable-gpu','--hide-scrollbars','--no-first-run','--force-device-scale-factor=1',f'--user-data-dir={directory / "chrome-profile"}','--window-size=720,1080','--run-all-compositor-stages-before-draw','--virtual-time-budget=1000',f'--screenshot={png}',(directory/'title.xhtml').as_uri()],capture_output=True,text=True)
        if proc.returncode or not png.exists(): raise RuntimeError(proc.stderr[-2000:])
        with Image.open(png) as im:
            if im.size!=(720,1080): raise ValueError(f'Unexpected cover size {im.size}')
            im.convert('RGB').save(cover,'JPEG',quality=92,optimize=True,progressive=False)
    entries['cover.jpg']=cover.read_bytes()
    description='An adult historical-fantasy mystery about a goblin accountant, missing wages and a death at a works in 1752. Unofficial Wizarding World fan fiction; first book of The Goblin Wars.'
    identifier='urn:uuid:'+str(uuid.uuid5(uuid.NAMESPACE_URL,'wizarding-world/goblin-wars/'+meta['id']))
    items='\n'.join(f'<item id="{Path(f).stem}" href="{f}" media-type="application/xhtml+xml"'+(' properties="nav"' if f=='nav.xhtml' else '')+'/>' for f in entries if f.endswith('.xhtml'))
    order=['title','about','nav']+[Path(c['file']).stem for c in chapters]
    spine=''.join(f'<itemref idref="{x}"/>' for x in order)
    entries['package.opf']=f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="{OPF}" version="3.0" unique-identifier="book-id" xml:lang="en" prefix="schema: http://schema.org/">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:identifier id="book-id">{identifier}</dc:identifier><dc:title>{escape(meta['title'])}</dc:title><dc:language>en</dc:language>
<dc:description>{escape(description)}</dc:description><dc:rights>Unofficial fan fiction. Free fan publication by the author; no affiliation with or endorsement by the rights holders.</dc:rights>
<meta property="dcterms:modified">2026-10-27T00:00:00Z</meta><meta property="rendition:layout">reflowable</meta>
<meta property="schema:accessMode">textual</meta><meta property="schema:accessModeSufficient">textual</meta>
<meta property="schema:accessibilityFeature">tableOfContents</meta><meta property="schema:accessibilityFeature">structuralNavigation</meta>
<meta property="schema:accessibilitySummary">Reflowable text with ordered headings, linked contents and landmarks. Screen-reader rendering has not been independently tested.</meta>
</metadata><manifest>{items}<item id="style" href="style.css" media-type="text/css"/><item id="cover-image" href="cover.jpg" media-type="image/jpeg" properties="cover-image"/></manifest>
<spine>{spine}</spine></package>'''
    container='''<?xml version="1.0" encoding="UTF-8"?><container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0"><rootfiles><rootfile full-path="EPUB/package.opf" media-type="application/oebps-package+xml"/></rootfiles></container>'''
    output=OUT/(meta['id']+'.epub')
    with ZipFile(output,'w') as archive:
        def add(name,value,compression=ZIP_DEFLATED):
            info=ZipInfo(name,(2026,10,27,0,0,0)); info.compress_type=compression
            archive.writestr(info,value if isinstance(value,bytes) else value.encode('utf-8'))
        add('mimetype','application/epub+zip',ZIP_STORED); add('META-INF/container.xml',container)
        for filename,value in entries.items(): add('EPUB/'+filename,value)
    with ZipFile(output) as archive:
        assert archive.testzip() is None
        assert archive.infolist()[0].filename=='mimetype' and archive.infolist()[0].compress_type==ZIP_STORED
        assert archive.read('mimetype')==b'application/epub+zip'
        for file in archive.namelist():
            if file.endswith(('.xml','.xhtml','.opf')): ET.fromstring(archive.read(file))
        package=ET.fromstring(archive.read('EPUB/package.opf'))
        assert [e.attrib['idref'] for e in package.find(f'{{{OPF}}}spine')]==order
        assert package.find('.//{http://purl.org/dc/elements/1.1/}creator') is None
        for ch in chapters:
            tree=ET.fromstring(archive.read('EPUB/'+ch['file']))
            assert ''.join(tree.find(f'.//{{{XHTML}}}h1').itertext())==ch['title']
            actual=[norm(''.join(p.itertext())) for p in tree.findall(f'.//{{{XHTML}}}p')]
            assert actual==ch['paragraphs'],ch['source']
        nav=ET.fromstring(archive.read('EPUB/nav.xhtml'))
        tocnode=nav.find(f'.//{{{XHTML}}}nav[@id="toc"]')
        assert [a.attrib['href'] for a in tocnode.findall(f'.//{{{XHTML}}}a')]==[x[0] for x in toc]
        for f in archive.namelist():
            if f.endswith('.xhtml'):
                raw=archive.read(f).decode('utf-8'); assert not TAG.search(raw),f
                tree=ET.fromstring(raw)
                for node in tree.iter():
                    for attr in ('src','href'):
                        if attr in node.attrib:
                            target=node.attrib[attr].split('#')[0]
                            assert 'EPUB/'+target in archive.namelist(),(f,target)
        assert archive.read('EPUB/cover.jpg')==cover.read_bytes()
    print(json.dumps({'epub':str(output),'sha256':sha(output.read_bytes()),'bytes':output.stat().st_size,'cover':str(cover),'cover_sha256':sha(cover.read_bytes()),'cover_bytes':cover.stat().st_size,'cover_derivation':'Exact 720×1080 Chrome rendering of the EPUB title.xhtml and style.css, converted to JPEG and embedded as cover-image','chapter_count':len(chapters),'source_sha256':sources,'checks':['ZIP and XML','reflowable metadata','source paragraph/title fidelity','chapter/spine/navigation order','local links','tag exclusion','no invented creator credit','embedded cover equals exported JPEG'],'limitations':['Not published; no EPUBCheck or physical-device review in builder','No franchise distribution rights established','Title-page JPEG rendering depends on local Chrome and fonts']},ensure_ascii=False,indent=2))

if __name__=='__main__': build()
