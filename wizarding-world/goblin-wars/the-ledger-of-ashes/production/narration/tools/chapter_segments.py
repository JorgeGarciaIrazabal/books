#!/usr/bin/env python3
"""Create and verify word-exact narration segments for an ordered chapter book.

The chapter Markdown is source. Headings become spoken chapter titles; paragraph
whitespace is normalised, not words or punctuation. Audio chunks never cross a
chapter boundary. JSON is intentionally private working data, not a page package.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path


def digest(data):
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def normalise(s):
    return re.sub(r'\s+', ' ', s).strip()


def split_chapter(path, limit):
    raw = path.read_text(encoding='utf-8')
    lines = raw.splitlines()
    if not lines or not lines[0].startswith('# '):
        raise ValueError(f'{path}: expected chapter heading')
    title = lines[0][2:].strip()
    text = normalise(title + '\n' + '\n'.join(lines[1:]))
    # Keep punctuation, quotation marks and words. Long sentences split only at
    # whitespace; record the exact rejoined text for whole-chapter verification.
    units = re.split(r'(?<=[.!?])\s+(?=[A-Z“"\'])', text)
    segments, current = [], []
    for unit in units:
        words = unit.split()
        if current and len(current) + len(words) > limit:
            segments.append(' '.join(current)); current = []
        while len(words) > limit:
            segments.append(' '.join(words[:limit])); words = words[limit:]
        current.extend(words)
    if current:
        segments.append(' '.join(current))
    if normalise(' '.join(segments)) != text:
        raise ValueError(f'{path}: segment reassembly mismatch')
    return raw, title, text, segments


def prepare(book, out, limit):
    manifest = json.loads((book / 'book.json').read_text())
    chapters = manifest['chapters']
    if not chapters or len(chapters) != len(set(chapters)):
        raise ValueError('Chapter order is missing or contains duplicates')
    rows, metadata = [], []
    for n, item in enumerate(chapters, 1):
        path = book / item
        raw, title, text, segments = split_chapter(path, limit)
        metadata.append({'chapter': n, 'path': item, 'title': title,
                         'source_sha256': digest(raw), 'spoken_sha256': digest(text),
                         'segments': len(segments)})
        for k, segment in enumerate(segments, 1):
            rows.append({'page': len(rows)+1, 'chapter': n, 'segment': k,
                         'text': segment, 'words': len(segment.split()),
                         'text_sha256': digest(segment)})
    data = {'schema_version': 1, 'kind': 'chapter_segments', 'max_words': limit,
            'chapters': metadata, 'pages': rows}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(f'{len(metadata)} chapters, {len(rows)} segments; exact text reassembly verified')


def verify(book, source):
    data = json.loads(source.read_text(encoding='utf-8'))
    actual_paths = json.loads((book / 'book.json').read_text())['chapters']
    if [x['path'] for x in data['chapters']] != actual_paths:
        raise ValueError('Chapter order or coverage differs')
    rows = data['pages']
    if [r['page'] for r in rows] != list(range(1, len(rows)+1)):
        raise ValueError('Segment numbers not contiguous')
    for meta in data['chapters']:
        raw, title, text, _ = split_chapter(book / meta['path'], data['max_words'])
        selected = [r for r in rows if r['chapter'] == meta['chapter']]
        if digest(raw) != meta['source_sha256'] or digest(text) != meta['spoken_sha256']:
            raise ValueError(f"Changed source: {meta['path']}")
        if len(selected) != meta['segments'] or [r['segment'] for r in selected] != list(range(1,len(selected)+1)):
            raise ValueError(f"Missing or duplicate segment: {meta['path']}")
        if any(digest(r['text']) != r['text_sha256'] for r in selected):
            raise ValueError(f"Segment hash mismatch: {meta['path']}")
        if normalise(' '.join(r['text'] for r in selected)) != text:
            raise ValueError(f"Words changed or reordered: {meta['path']}")
    print(f"Verified {len(data['chapters'])} chapters and {len(rows)} segments")


def make_script(data_path, script_path):
    data = json.loads(data_path.read_text(encoding='utf-8'))
    out = ['# Narration script', '', 'Single synthetic narrator; chapter titles are spoken once.']
    for row in data['pages']:
        out.extend(['', f"## Chapter {row['chapter']} · Segment {row['segment']}", '',
                    '```text', '<|speaker:0|> ' + row['text'], '```'])
    script_path.write_text('\n'.join(out)+'\n',encoding='utf-8')
    print(f"Wrote {len(data['pages'])} tagged segments")


def validate_script(data_path, script_path):
    data=json.loads(data_path.read_text(encoding='utf-8'))
    text=script_path.read_text(encoding='utf-8')
    pattern=re.compile(r'^## Chapter (\d+) · Segment (\d+)\n\n```text\n(.*?)\n```$',re.M|re.S)
    found=[(int(m.group(1)),int(m.group(2)),m.group(3)) for m in pattern.finditer(text)]
    rows=data['pages']
    if len(found)!=len(rows): raise ValueError(f'Script has {len(found)} segments; expected {len(rows)}')
    for (chapter,segment,tagged),row in zip(found,rows):
        if (chapter,segment)!=(row['chapter'],row['segment']): raise ValueError('Script segment order mismatch')
        if not tagged.startswith('<|speaker:0|> '): raise ValueError('Unexpected or missing narrator tag')
        if tagged[len('<|speaker:0|> '):]!=row['text']: raise ValueError(f'Script text differs at {chapter}/{segment}')
    print(f'Verified all {len(found)} tagged segments word for word')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['prepare','verify','script','validate-script'])
    p.add_argument('--book', type=Path, required=True)
    p.add_argument('--file', type=Path, required=True)
    p.add_argument('--max-words', type=int, default=110)
    p.add_argument('--script', type=Path)
    args = p.parse_args()
    if args.max_words < 20:
        p.error('--max-words must be at least 20')
    if args.action == 'prepare': prepare(args.book, args.file, args.max_words)
    elif args.action == 'verify': verify(args.book, args.file)
    elif args.action == 'script':
        if not args.script: p.error('--script is required')
        make_script(args.file,args.script)
    else:
        if not args.script: p.error('--script is required')
        verify(args.book,args.file); validate_script(args.file,args.script)

if __name__ == '__main__':
    main()
