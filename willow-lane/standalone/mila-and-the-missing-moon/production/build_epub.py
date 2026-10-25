#!/usr/bin/env python3
"""Build a reflowable EPUB 3 from book.json, using only the Python standard library."""
from pathlib import Path
from html import escape
import hashlib
import argparse
import json
import re
import uuid
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED
import xml.etree.ElementTree as ET

BOOK = Path(__file__).resolve().parents[1]
OUT = BOOK / 'exports'
XHTML = 'http://www.w3.org/1999/xhtml'
OPF = 'http://www.idpf.org/2007/opf'
EPUB = 'http://www.idpf.org/2007/ops'
AFTER = '''You can talk about these together, or just close the book and keep your favorite part.

Which clue first helped you guess where the moon had gone?

What did Mila believe before she had enough proof?

How did Noah help in a way Mila could not have managed alone?

If you had a detective notebook, what would you put on the first page?

Try this: choose an ordinary object in the room. Describe three things you can see about it without saying its name. Can someone guess what it is?'''
CSS = '''body { margin: 5%; font-family: serif; line-height: 1.5; }
p { margin: 0 0 0.75em; orphans: 2; widows: 2; }
h1 { font-size: 1.65em; line-height: 1.2; margin: 1.5em 0 1em; }
h1, h2 { break-after: avoid; page-break-after: avoid; }
.chapter-number { font-size: 0.85em; letter-spacing: 0.12em; margin-top: 2em; }
.chapter-number + h1 { margin-top: 0.4em; }
.title-page { text-align: center; margin-top: 15%; }
.ornament { font-size: 3em; margin: 0.7em 0; }
nav ol { padding-left: 1.6em; }
nav li { margin-bottom: 0.65em; }
'''


def inline(raw):
    text = escape(raw.replace('\n', ' '), quote=False)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    return re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', text)


def paragraphs(raw):
    return '\n'.join('<p>' + inline(p.strip()) + '</p>'
                     for p in re.split(r'\n\s*\n', raw.strip()) if p.strip())


def document(title, body, language='en'):
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="{XHTML}" xmlns:epub="{EPUB}" lang="{language}" xml:lang="{language}">
<head><meta charset="utf-8"/><title>{escape(title)}</title>
<link rel="stylesheet" type="text/css" href="style.css"/></head>
<body>{body}</body></html>'''


def normalized(text):
    return ' '.join(text.split())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--edition', choices=['es'], help='Build a translated edition')
    args = parser.parse_args()
    metadata_path = 'editions/es.json' if args.edition else 'book.json'
    meta = json.loads((BOOK / metadata_path).read_text())
    language = meta['language']
    if args.edition:
        original = json.loads((BOOK / 'book.json').read_text())
        if meta['source_chapters'] != original['chapters']:
            raise ValueError('Translation order must match book.json')
        if [Path(p).name for p in meta['chapters']] != [Path(p).name for p in original['chapters']]:
            raise ValueError('Missing or misordered translated chapter')
    chapter_label = 'CAPÍTULO' if language == 'es' else 'CHAPTER'
    contents_label = 'Índice' if language == 'es' else 'Contents'
    title_label = 'Portada' if language == 'es' else 'Title'
    after_title, after = 'A little more to wonder about', AFTER
    title = meta['title']
    entries = {}
    chapters = []
    sources = {}
    if 'afterword' in meta:
        after_path = BOOK / meta['afterword']
        after_heading, after = after_path.read_text().strip().split('\n', 1)
        after_title = after_heading.lstrip('# ').strip()
        sources[meta['afterword']] = hashlib.sha256(after_path.read_bytes()).hexdigest()
    for n, relative in enumerate(meta['chapters'], 1):
        path = BOOK / relative
        sources[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
        raw = path.read_text()
        heading, body = raw.strip().split('\n', 1)
        if not heading.startswith('# '):
            raise ValueError(f'Expected chapter heading in {relative}')
        name = re.sub(r'^\d+\.\s*', '', heading[2:].strip())
        # PDF pagination is layout metadata; paragraphs flow continuously in EPUB.
        body = body.replace('<!-- PAGEBREAK -->', '')
        if '<!--' in body:
            raise ValueError(f'Unexpected source comment in {relative}')
        filename = f'chapter-{n:02}.xhtml'
        content = (f'<section epub:type="chapter" role="doc-chapter" id="chapter-{n}">'
                   f'<p class="chapter-number">{chapter_label} {n}</p><h1>{escape(name)}</h1>'
                   f'{paragraphs(body)}</section>')
        entries[filename] = document(f'{n}. {name}', content, language)
        chapters.append((relative, filename, name, body))

    entries['title.xhtml'] = document(title, f'''<section class="title-page" epub:type="titlepage">
<p>{escape(meta.get('series_label', 'A WILLOW LANE MYSTERY'))}</p><h1>{escape(title)}</h1>
<p class="ornament" aria-hidden="true">☾ ✦</p>
<p>{escape(meta.get('tagline', 'A mystery to share, one chapter at a time'))}</p></section>''', language)
    entries['together.xhtml'] = document(after_title,
        '<section epub:type="afterword" role="doc-afterword"><h1>' + escape(after_title) + '</h1>'
        + paragraphs(after) + '</section>', language)
    links = [('title.xhtml', title_label)]
    links += [(filename, f'{n}. {name}') for n, (_, filename, name, _) in enumerate(chapters, 1)]
    links += [('together.xhtml', after_title)]
    toc = '\n'.join(f'<li><a href="{file}">{escape(label)}</a></li>' for file, label in links)
    entries['nav.xhtml'] = document(contents_label, f'''<nav epub:type="toc" id="toc" role="doc-toc">
<h1>{contents_label}</h1><ol>{toc}</ol></nav>''', language)
    entries['style.css'] = CSS
    identifier = 'urn:uuid:' + str(uuid.uuid5(uuid.NAMESPACE_URL, 'willow-lane/standalone/' + meta['id']))
    # A stable edition timestamp makes repeat builds byte-for-byte reproducible.
    modified = '2026-10-25T00:00:00Z'
    manifest = '\n'.join(f'<item id="{Path(file).stem}" href="{file}" media-type="application/xhtml+xml"'
                         + (' properties="nav"' if file == 'nav.xhtml' else '') + '/>'
                         for file in entries if file.endswith('.xhtml'))
    order = ['title', 'nav'] + [Path(c[1]).stem for c in chapters] + ['together']
    spine = ''.join(f'<itemref idref="{item}"/>' for item in order)
    entries['package.opf'] = f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="{OPF}" version="3.0" unique-identifier="book-id" xml:lang="{language}">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:identifier id="book-id">{identifier}</dc:identifier><dc:title>{escape(title)}</dc:title>
<dc:language>{language}</dc:language><dc:description>{escape(meta.get('description', 'A read-aloud detective mystery.'))}</dc:description>
<meta property="dcterms:modified">{modified}</meta>
<meta property="rendition:layout">reflowable</meta></metadata>
<manifest>{manifest}<item id="style" href="style.css" media-type="text/css"/></manifest>
<spine>{spine}</spine></package>'''
    container = '''<?xml version="1.0" encoding="UTF-8"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">
<rootfiles><rootfile full-path="EPUB/package.opf" media-type="application/oebps-package+xml"/>
</rootfiles></container>'''
    OUT.mkdir(exist_ok=True)
    output = OUT / (meta['id'] + '.epub')
    from zipfile import ZipInfo
    with ZipFile(output, 'w') as archive:
        def add(name, value, compression=ZIP_DEFLATED):
            info = ZipInfo(name, date_time=(2026, 10, 25, 0, 0, 0))
            info.compress_type = compression
            archive.writestr(info, value.encode('utf-8'))
        add('mimetype', 'application/epub+zip', ZIP_STORED)
        add('META-INF/container.xml', container)
        for filename, content in entries.items():
            add('EPUB/' + filename, content)

    # Verify the actual archive, not only the strings used to build it.
    with ZipFile(output) as archive:
        assert archive.testzip() is None
        first = archive.infolist()[0]
        assert first.filename == 'mimetype' and first.compress_type == ZIP_STORED
        assert archive.read('mimetype') == b'application/epub+zip'
        for file in archive.namelist():
            if file.endswith(('.xml', '.xhtml', '.opf')):
                ET.fromstring(archive.read(file))
        package = ET.fromstring(archive.read('EPUB/package.opf'))
        assert [x.attrib['idref'] for x in package.find(f'{{{OPF}}}spine')] == order
        after_tree = ET.fromstring(archive.read('EPUB/together.xhtml'))
        actual_after = ' '.join(''.join(p.itertext()) for p in after_tree.findall(f'.//{{{XHTML}}}p'))
        expected_after = ' '.join(''.join(p.itertext()) for p in ET.fromstring(f'<div>{paragraphs(after)}</div>'))
        assert normalized(actual_after) == normalized(expected_after)
        for relative, filename, name, raw in chapters:
            tree = ET.fromstring(archive.read('EPUB/' + filename))
            actual = [''.join(p.itertext()) for p in tree.findall(f'.//{{{XHTML}}}p')][1:]
            expected_tree = ET.fromstring(f'<div>{paragraphs(raw)}</div>')
            expected = [''.join(p.itertext()) for p in expected_tree]
            assert list(map(normalized, actual)) == list(map(normalized, expected)), relative
            # Independent source comparison, stripping only the supported emphasis markup.
            source_plain = re.sub(r'\*\*(.+?)\*\*', r'\1', raw)
            source_plain = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'\1', source_plain)
            assert normalized(' '.join(actual)) == normalized(source_plain), relative
        navigation = ET.fromstring(archive.read('EPUB/nav.xhtml'))
        assert [a.attrib['href'] for a in navigation.findall(f'.//{{{XHTML}}}a')] == [p[0] for p in links]
        for file in archive.namelist():
            if file.endswith('.xhtml'):
                tree = ET.fromstring(archive.read(file))
                assert tree.attrib['lang'] == language
                for node in tree.iter():
                    for attribute in ('href', 'src'):
                        if attribute in node.attrib:
                            target = node.attrib[attribute].split('#')[0]
                            assert 'EPUB/' + target in archive.namelist(), (file, target)
        assert b'PAGEBREAK' not in b''.join(archive.read(f) for f in archive.namelist())
    report = {
        'format': 'EPUB 3, reflowable', 'title': title, 'language': language,
        'chapter_count': len(chapters), 'source_sha256': sources,
        'builder_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'metadata_sha256': {metadata_path: hashlib.sha256((BOOK / metadata_path).read_bytes()).hexdigest()},
        'output': output.name, 'output_sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
        'checks': ['ZIP integrity and uncompressed first mimetype entry', 'XML parsing',
                   'chapter order matches book.json', 'all chapter paragraphs match source text',
                   'navigation order and all local links resolve', 'no printed pagination markers',
                   'afterword completeness and document language tags'],
        'limitations': ['Reader app rendering varies; not tested on a physical Android device.',
                        'Page count depends on screen size and reader settings.'],
    }
    report_name = f'epub-manifest-{language}.json' if args.edition else 'epub-manifest.json'
    (OUT / report_name).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    if args.edition:
        assembled = ['# ' + title, meta['description']]
        assembled.extend((BOOK / relative).read_text().strip() for relative in meta['chapters'])
        assembled.append((BOOK / meta['afterword']).read_text().strip())
        (OUT / (meta['id'] + '.md')).write_text('\n\n'.join(assembled) + '\n')
    print(json.dumps({'epub': str(output), 'chapters': len(chapters), 'bytes': output.stat().st_size,
                      'verification': 'passed'}))


if __name__ == '__main__':
    main()
