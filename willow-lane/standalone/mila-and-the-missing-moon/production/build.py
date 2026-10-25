#!/usr/bin/env python3
"""Build the fifty-page reading edition. Requires reportlab (and pypdf for QA)."""
from pathlib import Path
import hashlib
import argparse
import json
import math
import re
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, Color
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph

BOOK = Path(__file__).resolve().parents[1]
OUT = BOOK / 'exports'
W, H = 504, 720
INK = HexColor('#24394b')
GOLD = HexColor('#bd882a')
PAPER = HexColor('#fffcf5')
FONT_DIR = Path('/usr/share/fonts/truetype/dejavu')
for name, file in [('Story','DejaVuSerif.ttf'), ('StoryBold','DejaVuSerif-Bold.ttf'), ('StoryItalic','DejaVuSerif-Italic.ttf'), ('Label','DejaVuSans.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(FONT_DIR/file)))
pdfmetrics.registerFontFamily('Story',normal='Story',bold='StoryBold',italic='StoryItalic',boldItalic='StoryBold')
BODY = ParagraphStyle('body', fontName='Story', fontSize=13.2, leading=18.4, textColor=INK, spaceAfter=5.0)
HEADING = ParagraphStyle('heading',fontName='StoryBold',fontSize=21,leading=25,textColor=INK)
QUESTION = ParagraphStyle('question',parent=BODY,fontSize=12.5,leading=18,spaceAfter=14)

def inline(s):
    s=escape(s)
    s=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',s)
    return re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)',r'<i>\1</i>',s).replace('\n',' ')

def star(c,x,y,r=4):
    p=c.beginPath()
    for i in range(8):
        a=math.pi/2+i*math.pi/4
        q=r if i%2==0 else r*.3
        (p.moveTo if i==0 else p.lineTo)(x+math.cos(a)*q,y+math.sin(a)*q)
    p.close(); c.drawPath(p,fill=1,stroke=0)

def lantern(c,x,y,r=16):
    c.setStrokeColor(INK); c.setFillColor(GOLD); c.setLineWidth(1)
    c.line(x,y+r+16,x,y+r+5)
    c.ellipse(x-r*.8,y-r,x+r*.8,y+r,fill=0)
    c.ellipse(x-r*.35,y-r,x+r*.35,y+r,fill=0)
    c.line(x-r*.42,y+r,x+r*.42,y+r)
    c.line(x-r*.42,y-r,x+r*.42,y-r)
    c.circle(x,y,2,stroke=0,fill=1)

def vignette(c,n,x,y):
    c.saveState(); c.translate(x,y); c.setStrokeColor(GOLD); c.setFillColor(GOLD); c.setLineWidth(1.1)
    if n in (1,10,11):
        c.circle(0,0,12,fill=0); star(c,-22,7,3); star(c,24,-4,4)
        if n==10:
            c.line(-4,-8,5,5); c.line(-5,-3,1,-5); c.line(0,3,7,0)
    elif n in (2,4):
        c.circle(-10,-7,5); c.circle(14,-7,5); c.line(-17,0,20,0); c.line(-14,0,-14,17); c.line(-14,17,-22,17); c.rect(-8,2,20,13)
    elif n in (3,8,12):
        c.roundRect(-15,-12,30,27,2); c.line(-9,-11,-9,14)
        for yy in (-5,2,9): c.line(-5,yy,10,yy)
    elif n==5:
        c.arc(-19,-7,19,18,0,180); c.line(-19,5,19,5); c.line(0,5,0,-13); c.arc(-8,-17,0,-9,180,180)
        for xx in (-25,25): c.line(xx,10,xx-3,2)
    elif n==6:
        p=c.beginPath(); p.moveTo(-22,-10); p.lineTo(-8,-14); p.lineTo(6,-9); p.lineTo(22,-13); p.lineTo(22,12); p.lineTo(6,16); p.lineTo(-8,11); p.lineTo(-22,15); p.close(); c.drawPath(p)
        c.line(-8,-14,-8,11); c.line(6,-9,6,16); c.circle(12,4,3)
    else:
        c.rect(-16,-11,32,23); c.line(-16,12,0,19); c.line(0,19,16,12); c.line(0,-11,0,12); c.line(-16,12,0,5); c.line(0,5,16,12)
        if n==9: c.circle(8,-1,4)
    c.restoreState()

def base(c,page,label=None,chapter=None):
    c.setFillColor(PAPER); c.rect(0,0,W,H,fill=1,stroke=0)
    c.setFillColor(INK)
    if label:
        c.setFont('Label',8); c.drawCentredString(W/2,H-30,label)
    c.setStrokeColor(GOLD); c.setLineWidth(.4); c.line(48,39,W-48,39)
    c.setFont('Label',9); c.drawCentredString(W/2,23,str(page))
    c.setFillColor(GOLD); star(c,56,25,3); star(c,W-56,25,3)
    if chapter: vignette(c,chapter,W/2,H-62)

def draw_paragraphs(c,text,top,width=W-92,style=BODY,bottom=52):
    y=top
    for raw in re.split(r'\n\s*\n',text.strip()):
        if not raw.strip(): continue
        p=Paragraph(inline(raw.strip()),style)
        _,h=p.wrap(width,H)
        if y-h < bottom:
            raise ValueError(f'Page overflow: {getattr(c,"_pageNumber", "?")}, {y-h:.1f} < {bottom}; paragraph {raw[:90]!r}')
        p.drawOn(c,46,y-h)
        y-=h+style.spaceAfter
    return y

def words(s): return len(re.findall(r"\b[\w]+(?:['’\-][\w]+)*\b",s))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--edition',choices=['es'])
    args=parser.parse_args()
    OUT.mkdir(exist_ok=True)
    metadata_path='editions/es.json' if args.edition else 'book.json'
    meta=json.loads((BOOK/metadata_path).read_text())
    spanish=meta['language']=='es'
    if args.edition:
        original=json.loads((BOOK/'book.json').read_text())
        if meta['source_chapters']!=original['chapters'] or [Path(p).name for p in meta['chapters']]!=[Path(p).name for p in original['chapters']]:
            raise ValueError('Translation must follow book.json order')
    after_title='A little more to wonder about'
    after_override=None
    if 'afterword' in meta:
        heading,after_override=(BOOK/meta['afterword']).read_text().strip().split('\n',1)
        after_title=heading.lstrip('# ').strip()
    data=[]
    for i,relative in enumerate(meta['chapters'],1):
        text=(BOOK/relative).read_text()
        lines=text.strip().splitlines()
        title=lines[0].lstrip('# ').strip()
        title=re.sub(r'^(?:Chapter\s+)?\d+\s*[:.\-—]\s*','',title,flags=re.I)
        pages='\n'.join(lines[1:]).strip().split('<!-- PAGEBREAK -->')
        if len(pages)!=4: raise ValueError(f'{relative}: expected four page units, got {len(pages)}')
        data.append((relative,title,[p.strip() for p in pages]))
    if len(data)!=12: raise ValueError('Twelve chapters required')
    pdf=OUT/(meta['id']+'.pdf')
    c=canvas.Canvas(str(pdf),pagesize=(W,H),pageCompression=1)
    c.setTitle(meta['title']); c.setSubject(meta.get('description','A read-aloud detective mystery'))
    c.setAuthor('')
    c.setFillColor(PAPER); c.rect(0,0,W,H,fill=1,stroke=0)
    c.setFillColor(INK); c.setFont('Label',9); c.drawCentredString(W/2,H-59,meta.get('series_label','A WILLOW LANE MYSTERY'))
    title_lines=['Mila y la','luna perdida'] if spanish else ['Mila and the','Missing Moon']
    for text,y in zip(title_lines,[H-132,H-170]):
        c.setFont('StoryBold',29); c.drawCentredString(W/2,y,text)
    c.setFillColor(GOLD); c.circle(W/2,367,67,fill=1,stroke=0)
    c.setFillColor(PAPER); c.circle(W/2+30,386,53,fill=1,stroke=0)
    c.setFillColor(GOLD)
    for x,y,r in [(107,363,5),(306,392,6),(288,275,4),(126,262,4),(238,335,3)]: star(c,x,y,r)
    for x,y,r in [(W/2-113,205,20),(W/2,182,25),(W/2+113,205,20)]: lantern(c,x,y,r)
    c.setFillColor(INK); c.setFont('StoryItalic',11); c.drawCentredString(W/2,83,meta.get('tagline','A mystery to share, one chapter at a time'))
    c.bookmarkPage('title'); c.addOutlineEntry('Portada' if spanish else 'Title','title',level=0); c.showPage()
    assembled=['# '+meta['title'],meta.get('description','A read-aloud detective mystery.'),'<!-- PAGEBREAK -->']
    page_number=2; counts=[]
    for n,(relative,title,pages) in enumerate(data,1):
        assembled.append(f'# {"Capítulo" if spanish else "Chapter"} {n}: {title}')
        for unit,page in enumerate(pages):
            base(c,page_number,meta['title'].upper(),n if unit else None)
            if unit==0:
                c.bookmarkPage(f'chapter-{n}'); c.addOutlineEntry(f'{n}. {title}',f'chapter-{n}',level=0)
                c.setFillColor(GOLD); c.setFont('Label',9); c.drawCentredString(W/2,H-60,f'{"CAPÍTULO" if spanish else "CHAPTER"} {n}')
                p=Paragraph(escape(title),HEADING); _,hh=p.wrap(W-92,H); p.drawOn(c,46,H-77-hh)
                top=H-87-hh
            else: top=H-94
            draw_paragraphs(c,page,top)
            counts.append(words(page)); assembled += [page,'<!-- PAGEBREAK -->']
            c.showPage(); page_number+=1
    base(c,50,'DESPUÉS DEL CUENTO' if spanish else 'AFTER THE STORY')
    c.bookmarkPage('together'); c.addOutlineEntry(after_title,'together',level=0)
    c.setFillColor(INK); c.setFont('StoryBold',19); c.drawString(46,H-69,after_title)
    after='''You can talk about these together, or just close the book and keep your favorite part.

Which clue first helped you guess where the moon had gone?

What did Mila believe before she had enough proof?

How did Noah help in a way Mila could not have managed alone?

If you had a detective notebook, what would you put on the first page?

Try this: choose an ordinary object in the room. Describe three things you can see about it without saying its name. Can someone guess what it is?'''
    if after_override is not None: after=after_override.strip()
    draw_paragraphs(c,after,H-106,style=QUESTION)
    assembled += ['# '+after_title,after]
    c.showPage(); c.save()
    (OUT/(meta['id']+'.md')).write_text('\n\n'.join(assembled)+'\n')
    support=[metadata_path,'production/build.py']+([meta['afterword']] if 'afterword' in meta else [])
    manifest={'title':meta['title'],'pdf_pages':50,'story_pages':48,'chapters':12,'story_words':sum(counts),'words_per_story_page':counts,'source_sha256':{r:hashlib.sha256((BOOK/r).read_bytes()).hexdigest() for r,_,_ in data},'support_sha256':{r:hashlib.sha256((BOOK/r).read_bytes()).hexdigest() for r in support},'art':'Original vector drawings in build.py','dependencies':['reportlab'],'font':'DejaVu Serif 13.2 pt, 18.4 pt leading'}
    (OUT/('build-manifest-es.json' if spanish else 'build-manifest.json')).write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'pdf':str(pdf),'story_words':sum(counts),'page_word_range':[min(counts),max(counts)]}))

if __name__=='__main__': main()
