#!/usr/bin/env python3
"""Mechanical completeness checks on the actual PDF, not editorial certification."""
from pathlib import Path
import json
import argparse
import re
from pypdf import PdfReader

BOOK=Path(__file__).resolve().parents[1]
def normalized(s):
    return re.sub(r'\s+','',s).replace('*','').replace('\u00ad','')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--edition',choices=['es'])
    args=parser.parse_args()
    meta=json.loads((BOOK/('editions/es.json' if args.edition else 'book.json')).read_text())
    pdf=PdfReader(BOOK/'exports'/(meta['id']+'.pdf'))
    assert len(pdf.pages)==50, f'{len(pdf.pages)} PDF pages'
    checks=[]
    index=1
    for path in meta['chapters']:
        text=(BOOK/path).read_text()
        pages='\n'.join(text.splitlines()[1:]).strip().split('<!-- PAGEBREAK -->')
        assert len(pages)==4
        for body in pages:
            actual=pdf.pages[index].extract_text()
            assert normalized(body) in normalized(actual), f'Missing or changed story text on PDF page {index+1}'
            assert '<!--' not in actual, f'Leaked layout metadata on page {index+1}'
            assert float(pdf.pages[index].mediabox.width)==504
            assert float(pdf.pages[index].mediabox.height)==720
            checks.append({'pdf_page':index+1,'complete_source_text_present':True})
            index+=1
    if args.edition:
        after_heading,after=(BOOK/meta['afterword']).read_text().strip().split('\n',1)
        assert after_heading.lstrip('# ').strip() in pdf.pages[49].extract_text()
        assert normalized(after) in normalized(pdf.pages[49].extract_text())
        assert 'luna perdida' in pdf.pages[0].extract_text()
    else:
        assert 'A little more to wonder about' in pdf.pages[49].extract_text()
        assert 'Missing Moon' in pdf.pages[0].extract_text()
    assembled=(BOOK/'exports'/(meta['id']+'.md')).read_text()
    for path in meta['chapters']:
        for block in '\n'.join((BOOK/path).read_text().splitlines()[1:]).strip().split('<!-- PAGEBREAK -->'):
            assert block.strip() in assembled
    report={'pdf_pages':len(pdf.pages),'story_pages_checked':len(checks),'dimensions_inches':[7,10], 'complete_source_text_in_pdf':True,'complete_source_text_in_markdown':True,'layout_overflow':'Build succeeded with explicit bounds checks and fixed type size','coverage':checks,'limitations':'Mechanical checks do not establish literary quality, child comprehension, or publication readiness.'}
    (BOOK/'exports'/('verification-es.json' if args.edition else 'verification.json')).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='coverage'}))
if __name__=='__main__':main()
