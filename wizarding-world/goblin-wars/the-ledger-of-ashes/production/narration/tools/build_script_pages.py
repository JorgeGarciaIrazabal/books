#!/usr/bin/env python3
"""Adapter for shared validator: verify chapter-based narration, not page audio.

The shared validator uses a historical page-builder entry point. This adapter
checks the chapter-segment contract and exact assembled Markdown instead of
claiming that reflowable chapters are fixed pages.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def main():
    if len(sys.argv)!=4:
        print('usage: build_script_pages.py script.md source.md out.json',file=sys.stderr); return 2
    script,source,out=map(Path,sys.argv[1:]); book=Path(__file__).resolve().parents[3]
    data=book/'production/narration/segments.json'; helper=Path(__file__).with_name('chapter_segments.py')
    run=subprocess.run([sys.executable,str(helper),'validate-script','--book',str(book),'--file',str(data),'--script',str(script)],capture_output=True,text=True)
    if run.returncode:
        print(run.stderr or run.stdout,file=sys.stderr); return 1
    manifest=json.loads((book/'book.json').read_text())
    expected='\n\n'.join((book/x).read_text(encoding='utf-8').strip() for x in manifest['chapters'])+'\n'
    if source.read_text(encoding='utf-8')!=expected:
        print('Assembled source differs from ordered chapters',file=sys.stderr); return 1
    doc=json.loads(data.read_text(encoding='utf-8'))
    out.write_text(json.dumps({'source_sha256':hashlib.sha256(expected.encode()).hexdigest(),'kind':'chapter_segments','pages':doc['pages']},ensure_ascii=False,indent=2)+'\n')
    print(f"Verified chapter script, {len(doc['pages'])} internal segments")
    return 0
if __name__=='__main__': raise SystemExit(main())
