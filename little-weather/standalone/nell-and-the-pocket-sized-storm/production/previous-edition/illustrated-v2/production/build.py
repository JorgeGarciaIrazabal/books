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


def load_art(plan: dict, manifest: dict, pages: list[dict]) -> tuple[dict, list[dict]]:
    if plan["chapter_paths"] != manifest["chapters"]:
        raise ValueError("Illustration plan chapter order differs from book.json")
    lookup = {page["number"]: page for page in pages}
    by_page, ids, assets, records = {}, set(), set(), []
    counts = dict.fromkeys(manifest["chapters"], 0)
    for art in plan["illustrations"]:
        if art["id"] in ids or art["asset"] in assets or art["page"] in by_page:
            raise ValueError("Duplicate image ID, asset, or picture page")
        if lookup[art["page"]]["chapter"] != art["chapter"]:
            raise ValueError(f"Art {art['id']} is outside its declared chapter")
        if art["page"] < art["disclosure"]["not_before_page"]:
            raise ValueError(f"Early disclosure for {art['id']}")
        if not art.get("alt_text", "").strip():
            raise ValueError(f"Missing image alternative for {art['id']}")
        path = local_path(art["asset"])
        width_px, height_px = png_dimensions(path)
        max_w = float(art["placement"]["max_width_in"])
        max_h = float(art["placement"]["max_height_in"])
        if not 0 < max_w <= 6.26 or not 0 < max_h <= 2.5:
            raise ValueError(f"Unreviewed placement size for {art['id']}")
        scale = min(max_w / width_px, max_h / height_px)
        width_in, height_in = width_px * scale, height_px * scale
        # Keep original PNG masters; encode a high-quality placement derivative for the reading edition.
        derivative = EXPORTS / "illustration-derivatives" / f"{art['id'].lower()}.jpg"
        derivative.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(path) as original:
            options = {"quality": 92, "subsampling": 0, "optimize": True}
            if original.info.get("icc_profile"):
                options["icc_profile"] = original.info["icc_profile"]
            original.convert("RGB").save(derivative, "JPEG", **options)
        data_uri = "data:image/jpeg;base64," + base64.b64encode(derivative.read_bytes()).decode("ascii")
        by_page[art["page"]] = {**art, "data_uri": data_uri, "width_in": width_in, "height_in": height_in}
        records.append({"id": art["id"], "chapter": art["chapter"], "page": art["page"],
                        "asset": art["asset"], "sha256": sha256(path),
                        "placement_derivative": str(derivative.relative_to(BOOK)),
                        "placement_derivative_sha256": sha256(derivative),
                        "derivative_encoding": "JPEG quality92 4:4:4; unchanged dimensions; original PNG retained",
                        "native_pixels": [width_px, height_px],
                        "placed_inches": [round(width_in, 5), round(height_in, 5)],
                        "effective_ppi": [round(width_px / width_in, 2), round(height_px / height_in, 2)],
                        "fit": "contain, original proportions, no crop", "alt_text": art["alt_text"],
                        "plan_status_at_build": art["status"]})
        counts[art["chapter"]] += 1
        ids.add(art["id"]); assets.add(art["asset"])
    minimum, maximum = plan["art_per_chapter"]["min"], plan["art_per_chapter"]["max"]
    if any(not minimum <= count <= maximum for count in counts.values()):
        raise ValueError(f"Art frequency not met: {counts}")
    if len(records) != 12:
        raise ValueError("This edition requires exactly 12 story illustrations")
    return by_page, records


def main() -> None:
    manifest_path = BOOK / "book.json"
    manifest = json.loads(manifest_path.read_text())
    plan_path = local_path(manifest["illustration_plan"])
    plan = json.loads(plan_path.read_text())
    pages = read_pages(manifest)
    by_page, art_records = load_art(plan, manifest, pages)
    articles = []
    for page in pages:
        number = page["number"]
        art = by_page.get(number)
        paragraphs = "".join("<p>" + html.escape(p.replace("\n", " ")) + "</p>"
                             for p in re.split(r"\n\s*\n", page["text"]))
        title = '<h1>' + html.escape(manifest["title"]) + '</h1>' if number == 1 else ''
        picture = ''
        if art:
            picture = f'''<figure data-illustration="{art['id']}"><img src="{art['data_uri']}"
+              alt="{html.escape(art['alt_text'], quote=True)}" width="{round(art['width_in'] * 96)}"
+              height="{round(art['height_in'] * 96)}" style="width:{art['width_in']:.6f}in;height:{art['height_in']:.6f}in"></figure>'''.replace('\n+', '\n')
        header = f"{page['chapter_number']} · {page['chapter_title']}"
        articles.append(f'''<article class="page{' illustrated' if art else ''}{' opening' if number == 1 else ''}" id="page-{number}" aria-label="Page {number}">
<header><span>Nell &amp; Grumble</span><span>{html.escape(header)}</span></header>
<section class="content">{title}<div class="story">{paragraphs}</div>{picture}</section>
<footer><span class="rule"></span><span>{number}</span><span class="rule"></span></footer></article>''')
    document = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>''' + html.escape(manifest["title"]) + '''</title>
<style>
@page { size: 7.5in 9.5in; margin: 0; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body { background: #dce5e8; color: #233b45; font-family: "Noto Serif", "DejaVu Serif", serif; }
.page { background: #fffdf7; width: 7.5in; height: 9.5in; padding: .40in .62in .48in;
 position: relative; break-after: page; page-break-after: always; margin: 22px auto;
 box-shadow: 0 5px 30px #1e344222; }
.page:last-child { break-after: auto; page-break-after: auto; }
header { display: flex; justify-content: space-between; align-items: baseline;
 font-family: "Noto Sans", sans-serif; font-size: 8pt; color: #547681; line-height: 1.25;
 border-bottom: 1px solid #dbe5e6; padding-bottom: .10in; gap: .18in; }
header span:first-child { letter-spacing: .6px; white-space: nowrap; }
header span:last-child { text-align: right; }
.content { padding-top: .18in; }
h1 { font-size: 28pt; line-height: 1.14; font-weight: 700; letter-spacing: -.4px;
 margin: .08in 0 .28in; color: #254e60; max-width: 5.8in; }
.story { font-size: 16.8pt; line-height: 1.28; }
p { margin: 0 0 .075in; orphans: 2; widows: 2; }
p:last-child { margin-bottom: 0; }
figure { margin: .14in 0 0; display: flex; justify-content: center; align-items: center; }
figure img { display: block; object-fit: contain; max-width: 100%; }
footer { position: absolute; bottom: .27in; left: .62in; right: .62in; display: flex;
 align-items: center; gap: .15in; color: #547681; font-family: "Noto Sans", sans-serif;
 font-size: 9pt; line-height: 1; }
.rule { height: 1px; background: #dbe5e6; flex: 1; }
@media print {
 html, body { background: #fffdf7; print-color-adjust: exact; -webkit-print-color-adjust: exact; }
 .page { margin: 0; box-shadow: none; }
}
</style></head><body>''' + "\n".join(articles) + '''
<script id="layout-report" type="application/json">{}</script>
<script>
function checkLayout() {
 // The load event waits for the embedded image resources. Measure synchronously
 // so headless --dump-dom cannot serialize an unfinished async placeholder.
 const pages = [...document.querySelectorAll('.page')];
 const failures = [];
 const measurements = pages.map(page => {
   const bounds = page.getBoundingClientRect();
   const content = page.querySelector('.content').getBoundingClientRect();
   const footer = page.querySelector('footer').getBoundingClientRect();
   const picture = page.querySelector('img');
   const imageBox = picture ? picture.getBoundingClientRect() : null;
   const story = page.querySelector('.story').getBoundingClientRect();
   const errors = [];
   if (content.bottom + 12 > footer.top) errors.push('content/footer clearance');
   if (page.scrollWidth > page.clientWidth || page.scrollHeight > page.clientHeight) errors.push('page overflow');
   if (picture && (!picture.complete || !picture.naturalWidth)) errors.push('image not decoded');
   if (imageBox && imageBox.top < story.bottom) errors.push('image/text collision');
   if (imageBox && (imageBox.left < bounds.left || imageBox.right > bounds.right)) errors.push('image horizontal overflow');
   if (errors.length) failures.push({page:page.id, errors});
   return {page:Number(page.id.slice(5)), body_font_px:getComputedStyle(page.querySelector('.story')).fontSize,
     footer_clearance_px:Math.round((footer.top-content.bottom)*100)/100,
     image:picture ? {id:picture.parentElement.dataset.illustration, decoded:picture.complete && picture.naturalWidth>0,
       natural_pixels:[picture.naturalWidth,picture.naturalHeight], rendered_pixels:[imageBox.width,imageBox.height],
       alt:picture.alt} : null};
 });
 const report = {pages:pages.length, image_count:document.images.length, failures, measurements};
 document.querySelector('#layout-report').textContent = JSON.stringify(report);
 document.body.dataset.layout = failures.length ? 'failed' : 'passed';
}
if (document.readyState === 'complete') checkLayout();
else window.addEventListener('load', checkLayout, {once:true});
</script></body></html>'''
    EXPORTS.mkdir(exist_ok=True)
    html_path = EXPORTS / f"{STEM}.html"
    pdf_path = EXPORTS / f"{STEM}.pdf"
    html_path.write_text(document, encoding="utf-8")
    chrome = shutil.which("google-chrome") or shutil.which("chromium")
    if not chrome:
        raise RuntimeError("Local Chrome or Chromium is required")
    with tempfile.TemporaryDirectory(prefix="nell-illustrated-chrome-") as profile:
        command = [chrome, "--headless=new", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
                   "--window-size=900,1200", f"--user-data-dir={profile}", "--no-pdf-header-footer",
                   "--run-all-compositor-stages-before-draw", "--virtual-time-budget=5000",
                   f"--print-to-pdf={pdf_path}", "--dump-dom", html_path.as_uri()]
        result = subprocess.run(command, text=True, capture_output=True, timeout=60)
        if result.returncode:
            raise RuntimeError(result.stderr[-3000:])
        report_match = re.search(r'<script id="layout-report" type="application/json">(.*?)</script>', result.stdout, re.DOTALL)
        if not report_match:
            raise RuntimeError("Browser did not return layout report")
        layout = json.loads(html.unescape(report_match.group(1)))
        if layout.get("pages") != 30 or layout.get("image_count") != 12 or layout.get("failures"):
            raise RuntimeError(f"Layout validation failed: {layout.get('failures', layout)}")
    (EXPORTS / "illustrated-layout-check.json").write_text(json.dumps(layout, indent=2) + "\n")
    details = subprocess.run(["pdfinfo", str(pdf_path)], text=True, capture_output=True, check=True).stdout
    if not re.search(r"^Pages:\s+30$", details, re.MULTILINE):
        raise RuntimeError("Actual PDF does not have exactly 30 pages")
    inputs = [manifest_path, plan_path, *[local_path(p) for p in manifest["chapters"]],
              *[local_path(a["asset"]) for a in plan["illustrations"]], Path(__file__)]
    for relative in ["production/visual-style.md", "production/art-direction.md", "assets/references/cast-reference-v1.png"]:
        if (BOOK / relative).is_file(): inputs.append(BOOK / relative)
    # Include all references/prompts explicitly named in final provenance when supplied.
    for item in plan["illustrations"]:
        provenance = item.get("provenance", {})
        if provenance.get("prompt_record"): inputs.append(local_path(provenance["prompt_record"]))
        for reference in provenance.get("reference_assets", []):
            relative = reference if isinstance(reference, str) else reference.get("path")
            if relative: inputs.append(local_path(relative))
    inputs.extend(local_path(a["placement_derivative"]) for a in art_records)
    hashes = {str(path.relative_to(BOOK)): sha256(path) for path in [*dict.fromkeys(inputs), html_path, pdf_path]}
    record = {"schema_version": 1, "title": manifest["title"], "edition": manifest.get("edition"),
              "purpose": "private digital read-aloud proof candidate; no printer-ready claim",
              "story_pages": 30, "pdf_pages": 30, "page_size_inches": list(PAGE_IN),
              "chapter_order": manifest["chapters"], "body_type_points": BODY_PT,
              "body_leading": 1.28, "paragraph_gap_inches": .075,
              "illustration_count": len(art_records), "illustrations": art_records,
              "layout_overflow": [], "browser_layout_report": "exports/illustrated-layout-check.json",
              "sha256": hashes, "build": "python3 production/build.py",
              "renderer": subprocess.run([chrome, "--version"], capture_output=True, text=True, check=True).stdout.strip(),
              "accessibility": "Meaningful image alternatives embedded in self-contained HTML. PDF tagging/alt preservation requires separate verification; no accessibility certification.",
              "review_limit": "Build checks do not certify narrative art fidelity or final visual approval."}
    (EXPORTS / "reading-edition-manifest.json").write_text(json.dumps(record, indent=2) + "\n")
    print(f"Built {pdf_path}\n30 pages; 12 decoded story illustrations; 16.8 pt body type; no detected overlap.")


if __name__ == "__main__":
    main()
