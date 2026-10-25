#!/usr/bin/env python3
"""Build the 30-page reading edition from book.json, using local Chrome."""
from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

BOOK = Path(__file__).resolve().parents[1]
EXPORTS = BOOK / "exports"
STEM = "nell-and-the-pocket-sized-storm"


def ornament(kind: str) -> str:
    drawings = {
        "cloud": '''<path fill="#dcecf0" d="M24 57C5 57 6 32 25 31C22 11 53 6 61 26C77 13 98 26 94 40C116 43 107 62 91 60H24Z"/>
          <path d="M39 67l-3 7m25-7l-3 7m25-7l-3 7"/>
          <path d="M38 33l7-3m22 0l7 3M48 46q8 6 16 0"/><circle cx="45" cy="39" r="1.5" fill="#234957"/><circle cx="68" cy="39" r="1.5" fill="#234957"/>''',
        "kite": '''<path d="M60 8L88 33L60 60L34 33Z" fill="#dc705d"/><path d="M60 8v52M34 33h54"/>
          <path d="M60 60c-28 14 32 9 5 23"/><path d="M47 70l-8-4v8Z" fill="#eac477"/>
          <path d="M23 17h14M16 26h12M89 62h17"/>''',
        "band": '''<path d="M30 32h58v24q-2 12-28 12T30 56Z" fill="#eac477"/><path d="M88 37h18v9H88M27 32h64"/>
          <path d="M44 13l9 24m19-25L62 37"/><circle cx="43" cy="11" r="4" fill="#dc705d"/><circle cx="73" cy="10" r="4" fill="#dc705d"/>
          <path d="M16 43V25l10-3v16m71-17V8l9-2"/><ellipse cx="13" cy="43" rx="4" ry="3" fill="#234957"/><ellipse cx="23" cy="38" rx="4" ry="3" fill="#234957"/>''',
        "boot": '''<path d="M38 15h31v34h15q16 1 16 17v5H38Z" fill="#eac477"/><path d="M35 15h37M38 61h62M46 23v23"/>''',
    }
    if kind == "rainbow-boot":
        return ornament("boot").replace("</svg>", '<path d="M80 31q16-21 30 0" stroke="#dc705d"/><path d="M84 33q12-16 23 0" stroke="#eac477"/><path d="M88 35q8-11 16 0" stroke="#9abeb9"/></svg>')
    return '<svg aria-hidden="true" viewBox="0 0 120 86" fill="none" stroke="#234957" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">' + drawings[kind] + "</svg>"


def main() -> None:
    manifest = json.loads((BOOK / "book.json").read_text())
    title = manifest["title"]
    source_paths = [BOOK / name for name in manifest["chapters"]]
    source = "\n\n".join(path.read_text(encoding="utf-8") for path in source_paths)
    pieces = re.split(r"^## Page (\d+)\s*$", source, flags=re.MULTILINE)
    pages = [(int(pieces[i]), pieces[i + 1].strip()) for i in range(1, len(pieces), 2)]
    if [n for n, _ in pages] != list(range(1, 31)):
        raise ValueError("Expected exactly 30 consecutive story pages")
    if "\u2014" in source:
        raise ValueError("Manuscript contains an em dash, contrary to the style guide")
    articles = []
    for number, text in pages:
        kind = "boot" if number <= 4 or number >= 28 else "kite" if number in (6, 7) or 21 <= number <= 27 else "band" if 14 <= number <= 20 else "cloud"
        if number == 30:
            kind = "rainbow-boot"
        paragraphs = []
        for para in re.split(r"\n\s*\n", text):
            escaped = html.escape(para.replace("\n", " "))
            paragraphs.append(f"<p>{escaped}</p>")
        heading = f"<h1>{html.escape(title)}</h1>" if number == 1 else ""
        articles.append(f'''<article class="page{' opening' if number == 1 else ''}" id="page-{number}" aria-label="Page {number}">
          <header><span>Nell &amp; Grumble</span><span class="tiny-dots">&#9679; &nbsp; &#9679; &nbsp; &#9679;</span></header>
          <div class="ornament">{ornament(kind)}</div>
          {heading}<main>{''.join(paragraphs)}</main>
          <footer><span class="footer-line"></span><span>{number}</span><span class="footer-line"></span></footer>
        </article>''')
    document = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>''' + html.escape(title) + '''</title>
<style>
@page { size: 7.5in 9.5in; margin: 0; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body { background: #dce5e8; color: #233b45; font-family: "Noto Serif", "DejaVu Serif", serif; }
.page { background: #fffdf7; width: 7.5in; height: 9.5in; padding: .42in .66in .52in;
  position: relative; break-after: page; page-break-after: always; margin: 22px auto; box-shadow: 0 5px 30px #1e344222; }
.page:last-child { break-after: auto; page-break-after: auto; }
header { display: flex; justify-content: space-between; align-items: center; font-family: "Noto Sans", sans-serif;
  font-size: 8pt; letter-spacing: 1.2px; text-transform: uppercase; color: #547681;
  border-bottom: 1px solid #dbe5e6; padding-bottom: .12in; }
.tiny-dots { color: #cf785e; font-size: 5pt; }
.ornament { height: .91in; display: flex; align-items: center; justify-content: center; }
.ornament svg { width: 1.03in; height: .74in; }
h1 { font-size: 27pt; line-height: 1.18; font-weight: 700; letter-spacing: -.5px; margin: 0 0 .19in; color: #254e60; }
.opening .ornament { height: .66in; }
.opening .ornament svg { height: .59in; }
main { font-size: 16.8pt; line-height: 1.36; }
p { margin: 0 0 .105in; orphans: 2; widows: 2; }
p:last-child { margin-bottom: 0; }
footer { position: absolute; bottom: .29in; left: .66in; right: .66in; display: flex; align-items: center; gap: .15in;
  color: #547681; font-family: "Noto Sans", sans-serif; font-size: 9pt; }
.footer-line { height: 1px; background: #dbe5e6; flex: 1; }
@media print {
  html, body { background: #fffdf7; print-color-adjust: exact; -webkit-print-color-adjust: exact; }
  .page { margin: 0; box-shadow: none; }
}
@media screen and (max-width: 740px) {
  body { padding: 10px; }
  .page { margin: 0 auto 18px; width: 100%; height: auto; min-height: 9in; padding: .32in; }
  main { font-size: 16pt; }
  footer { left: .32in; right: .32in; }
}
</style></head><body>''' + "\n".join(articles) + '''
<script>
document.fonts.ready.then(() => {
  const bad = [...document.querySelectorAll('.page')].filter(p =>
    p.querySelector('main').getBoundingClientRect().bottom + 12 > p.querySelector('footer').getBoundingClientRect().top
    || p.scrollWidth > p.clientWidth);
  document.body.setAttribute('data-overflow', bad.map(p => p.id).join(','));
  document.body.setAttribute('data-pages', document.querySelectorAll('.page').length);
});
</script></body></html>'''
    EXPORTS.mkdir(exist_ok=True)
    html_path = EXPORTS / f"{STEM}.html"
    pdf_path = EXPORTS / f"{STEM}.pdf"
    html_path.write_text(document, encoding="utf-8")
    chrome = shutil.which("google-chrome") or shutil.which("chromium")
    if not chrome:
        raise RuntimeError("Local Chrome or Chromium is required for PDF generation")
    with tempfile.TemporaryDirectory(prefix="nell-book-chrome-") as profile:
        command = [chrome, "--headless=new", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
                   f"--user-data-dir={profile}", "--no-pdf-header-footer", "--run-all-compositor-stages-before-draw",
                   "--virtual-time-budget=2000", f"--print-to-pdf={pdf_path}", "--dump-dom", html_path.as_uri()]
        result = subprocess.run(command, text=True, capture_output=True, timeout=60)
        if result.returncode:
            raise RuntimeError(result.stderr[-3000:])
        if 'data-overflow=""' not in result.stdout or 'data-pages="30"' not in result.stdout:
            diagnostic = re.search(r'<body[^>]*>', result.stdout)
            raise RuntimeError(f"Layout check did not pass: {diagnostic.group() if diagnostic else 'no body'}")
    details = subprocess.run(["pdfinfo", str(pdf_path)], text=True, capture_output=True, check=True).stdout
    if not re.search(r"^Pages:\s+30$", details, flags=re.MULTILINE):
        raise RuntimeError("PDF must contain exactly 30 pages")
    hashes = {str(path.relative_to(BOOK)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in [BOOK / "book.json", *source_paths, Path(__file__), html_path, pdf_path]}
    (EXPORTS / "reading-edition-manifest.json").write_text(json.dumps({
        "title": title, "story_pages": 30, "pdf_pages": 30, "page_size_inches": [7.5, 9.5],
        "body_type_points": 16.8, "layout_overflow": [], "sha256": hashes,
        "build": "python3 production/build.py", "renderer": subprocess.run([chrome, "--version"], capture_output=True, text=True).stdout.strip()
    }, indent=2) + "\n")
    print(f"Built {pdf_path}\n30 PDF pages; no detected text/footer overlap or horizontal overflow.")


if __name__ == "__main__":
    main()
