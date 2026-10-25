#!/usr/bin/env python3
"""Package the approved illustrated-v3 compositions as a fixed-layout EPUB 3.

Uses real XHTML text and original images, not screenshots of story pages.
The first-page PDF render is used only as the library thumbnail.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import uuid
import xml.etree.ElementTree as ET
import zipfile

BOOK = Path(__file__).resolve().parents[1]
EXPORTS = BOOK / "exports"
STEM = "nell-and-the-pocket-sized-storm"
EPUB_NS = "http://www.idpf.org/2007/ops"
XHTML_NS = "http://www.w3.org/1999/xhtml"
FONTS = ["NotoSerif-Regular.ttf", "NotoSerif-Bold.ttf", "NotoSans-Regular.ttf"]
LICENSE = Path("/usr/share/doc/fonts-noto-core/copyright")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def child(parent: ET.Element, tag: str, text: str | None = None, **attrs) -> ET.Element:
    node = ET.SubElement(parent, tag, attrs)
    node.text = text
    return node


def write_xml(path: Path, root: ET.Element) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(ET.tostring(root, encoding="utf-8", xml_declaration=True))


def document(title: str, viewport: bool = True) -> tuple[ET.Element, ET.Element]:
    root = ET.Element("html", {"xmlns": XHTML_NS, "xmlns:epub": EPUB_NS,
                               "lang": "en", "xml:lang": "en"})
    head = child(root, "head")
    child(head, "title", title)
    child(head, "meta", charset="utf-8")
    if viewport:
        child(head, "meta", name="viewport", content="width=720,height=912")
        child(head, "link", rel="stylesheet", type="text/css", href="../styles/book.css")
    return root, child(root, "body")


class ArticleParser(HTMLParser):
    """Turn the approved HTML fragment into well-formed XHTML without a converter."""
    VOID = {"img", "br", "hr", "meta", "link", "input", "wbr", "source"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = None
        self.stack = []

    def handle_starttag(self, tag, attrs):
        node = ET.Element(tag, {k: v or "" for k, v in attrs})
        if self.stack:
            self.stack[-1].append(node)
        else:
            if self.root is not None:
                raise ValueError("Multiple fragment roots")
            self.root = node
        if tag not in self.VOID:
            self.stack.append(node)

    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        if not self.stack or self.stack[-1].tag != tag:
            raise ValueError(f"Unexpected closing tag {tag}")
        self.stack.pop()

    def handle_data(self, data):
        if not self.stack:
            if data.strip():
                raise ValueError("Text outside article")
            return
        parent = self.stack[-1]
        if len(parent):
            parent[-1].tail = (parent[-1].tail or "") + data
        else:
            parent.text = (parent.text or "") + data


def main() -> None:
    book_path = BOOK / "book.json"
    book = json.loads(book_path.read_text())
    reading_manifest = EXPORTS / "reading-edition-manifest.json"
    approved = json.loads(reading_manifest.read_text())
    for relative, expected in approved["sha256"].items():
        if sha(BOOK / relative) != expected:
            raise ValueError(f"Approved reading input changed: {relative}")
    source_html = EXPORTS / f"{STEM}.html"
    source_pdf = EXPORTS / f"{STEM}.pdf"
    source = source_html.read_text()
    fragments = re.findall(r"<article\b.*?</article>", source, re.DOTALL)
    if len(fragments) != 30:
        raise ValueError("Expected exactly 30 approved page compositions")
    plan_path = BOOK / book["illustration_plan"]
    plan = json.loads(plan_path.read_text())
    by_page = {a["page"]: a for a in plan["illustrations"]}
    design_path = BOOK / book["layout"]
    design = json.loads(design_path.read_text())
    package = EXPORTS / "epub"
    for folder in ["META-INF", "EPUB/pages", "EPUB/styles", "EPUB/images", "EPUB/fonts", "EPUB/licenses"]:
        (package / folder).mkdir(parents=True, exist_ok=True)
    resources = {}
    manifest_items = []

    def resource(relative: str, data: bytes, mime: str, identifier: str, properties: str = ""):
        path = package / relative
        path.write_bytes(data)
        resources[relative] = path
        attrs = {"id": identifier, "href": relative.removeprefix("EPUB/"), "media-type": mime}
        if properties:
            attrs["properties"] = properties
        manifest_items.append(attrs)

    for name in FONTS:
        path = Path("/usr/share/fonts/truetype/noto") / name
        resource(f"EPUB/fonts/{name}", path.read_bytes(), "font/ttf", name.removesuffix(".ttf"))
    resource("EPUB/licenses/noto-copyright.txt", LICENSE.read_bytes(), "text/plain", "font-license")
    for art in plan["illustrations"]:
        resource(f"EPUB/images/{art['id'].lower()}.png", (BOOK / art["asset"]).read_bytes(),
                 "image/png", art["id"].lower())
    # A library thumbnail only: no extra cover, story page or spine item is added.
    with tempfile.TemporaryDirectory(prefix="nell-epub-cover-") as temp:
        prefix = Path(temp) / "cover"
        subprocess.run(["pdftoppm", "-f", "1", "-l", "1", "-r", "144", "-singlefile",
                        "-jpeg", "-jpegopt", "quality=90", str(source_pdf), str(prefix)],
                       check=True, capture_output=True)
        resource("EPUB/images/cover.jpg", prefix.with_suffix(".jpg").read_bytes(),
                 "image/jpeg", "cover", "cover-image")

    css = re.search(r"<style>(.*?)</style>", source, re.DOTALL).group(1)
    # EPUB pages each have their own canvas; remove browser preview furniture.
    css = css[:css.index("@media print")]
    css = css.replace("p{margin:0 0 var(--paragraph-gap);", "p{margin:0;")
    css = css.replace('.page:has(figure[data-background="true"])', ".page.background")
    faces = "\n".join([
        '@font-face{font-family:"Noto Serif";font-style:normal;font-weight:400;src:url("../fonts/NotoSerif-Regular.ttf") format("truetype")}',
        '@font-face{font-family:"Noto Serif";font-style:normal;font-weight:700;src:url("../fonts/NotoSerif-Bold.ttf") format("truetype")}',
        '@font-face{font-family:"Noto Sans";font-style:normal;font-weight:400;src:url("../fonts/NotoSans-Regular.ttf") format("truetype")}',
    ])
    css = faces + "\n" + css + "\nhtml,body{width:720px;height:912px;background:#fffdf7;overflow:hidden}\n.page{margin:0;box-shadow:none;break-after:auto;page-break-after:auto}\n.page-marker{position:absolute;width:0;height:0;overflow:hidden}\n"
    resource("EPUB/styles/book.css", css.encode(), "text/css", "book-css")

    for number, fragment in enumerate(fragments, 1):
        parser = ArticleParser()
        parser.feed(fragment)
        parser.close()
        if parser.stack:
            raise ValueError(f"Unclosed page {number}")
        article = parser.root
        article.set("id", f"canvas-{number}")
        article.attrib.pop("data-quiet-zone", None)
        chapter = next(c for c in book["chapter_details"] if c["pages"][0] <= number <= c["pages"][1])
        root, body = document(f"{chapter['title']} · Page {number}")
        body.set("epub:type", "bodymatter")
        body.append(article)
        marker = ET.Element("span", {"id": f"page-{number}", "epub:type": "pagebreak",
                                    "role": "doc-pagebreak", "aria-label": str(number), "class": "page-marker"})
        article.insert(0, marker)
        figure = article.find("figure")
        if figure is not None:
            image = figure.find("img")
            art = by_page[number]
            if image.get("alt") != art["alt_text"]:
                raise ValueError(f"Stale image alternative on page {number}")
            image.set("src", f"../images/{art['id'].lower()}.png")
            if figure.get("data-background") == "true":
                article.set("class", article.get("class") + " background")
            # Prose first in assistive reading order; absolute visual placement is unchanged.
            article.remove(figure)
            article.insert(len(article) - 1, figure)
        entry = design["pages"][number - 1]
        for block in article.findall("div[@class='story']"):
            block.set("style", re.sub(r"--paragraph-gap:[^;]+;?", "", block.get("style")))
            paragraphs = block.findall("p")
            for index, paragraph in enumerate(paragraphs):
                gap = 0 if index == len(paragraphs)-1 else entry["paragraph_gap_in"]
                paragraph.set("style", f"margin-bottom:{gap}in")
        article.find("footer").set("aria-hidden", "true")
        relative = f"EPUB/pages/page-{number:03d}.xhtml"
        data = ET.tostring(root, encoding="utf-8", xml_declaration=True)
        resource(relative, data, "application/xhtml+xml", f"page-{number:03d}")

    root, body = document(book["title"] + " · Contents", viewport=False)
    nav = child(body, "nav", **{"epub:type": "toc", "id": "toc"})
    child(nav, "h1", "Contents")
    listing = child(nav, "ol")
    for index, chapter in enumerate(book["chapter_details"], 1):
        child(child(listing, "li"), "a", f"{index}. {chapter['title']}",
              href=f"pages/page-{chapter['pages'][0]:03d}.xhtml")
    nav = child(body, "nav", **{"epub:type": "page-list", "id": "page-list", "hidden": "hidden"})
    child(nav, "h2", "Pages")
    listing = child(nav, "ol")
    for number in range(1,31):
        child(child(listing, "li"), "a", str(number), href=f"pages/page-{number:03d}.xhtml#page-{number}")
    nav = child(body, "nav", **{"epub:type": "landmarks", "hidden": "hidden"})
    child(child(child(nav, "ol"), "li"), "a", "Start reading",
          **{"epub:type": "bodymatter", "href": "pages/page-001.xhtml"})
    resource("EPUB/nav.xhtml", ET.tostring(root, encoding="utf-8", xml_declaration=True),
             "application/xhtml+xml", "nav", "nav")

    old_manifest = EXPORTS / "epub-manifest.json"
    old = json.loads(old_manifest.read_text()) if old_manifest.is_file() else {}
    modified = old.get("modified_utc") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    identifier = "urn:uuid:" + str(uuid.uuid5(uuid.NAMESPACE_URL, "little-weather/standalone/" + book["id"] + "/illustrated-v3-epub"))
    opf = ET.Element("package", {"xmlns": "http://www.idpf.org/2007/opf", "xmlns:dc": "http://purl.org/dc/elements/1.1/",
                                "version": "3.0", "unique-identifier": "book-id", "xml:lang": "en"})
    metadata = child(opf, "metadata")
    child(metadata, "dc:identifier", identifier, id="book-id")
    child(metadata, "dc:title", book["title"])
    child(metadata, "dc:language", "en")
    for property_name, value in [("dcterms:modified", modified), ("rendition:layout", "pre-paginated"),
                                 ("rendition:orientation", "auto"), ("rendition:spread", "none"),
                                 ("schema:accessMode", "textual"), ("schema:accessMode", "visual"),
                                 ("schema:accessibilityFeature", "tableOfContents"),
                                 ("schema:accessibilityFeature", "readingOrder"),
                                 ("schema:accessibilityFeature", "alternativeText"),
                                 ("schema:accessibilitySummary", "Fixed-layout illustrated pages with real text, image alternatives, chapter navigation and page navigation. Text resizing requires page zoom; no accessibility certification is claimed.")]:
        child(metadata, "meta", value, property=property_name)
    manifest = child(opf, "manifest")
    for item in manifest_items:
        ET.SubElement(manifest, "item", item)
    spine = child(opf, "spine", **{"page-progression-direction": "ltr"})
    for number in range(1,31):
        child(spine, "itemref", idref=f"page-{number:03d}", linear="yes")
    write_xml(package / "EPUB/package.opf", opf)
    resources["EPUB/package.opf"] = package / "EPUB/package.opf"
    container = ET.Element("container", {"xmlns": "urn:oasis:names:tc:opendocument:xmlns:container", "version": "1.0"})
    child(child(container, "rootfiles"), "rootfile", **{"full-path": "EPUB/package.opf", "media-type": "application/oebps-package+xml"})
    write_xml(package / "META-INF/container.xml", container)
    resources["META-INF/container.xml"] = package / "META-INF/container.xml"
    (package / "mimetype").write_bytes(b"application/epub+zip")
    resources["mimetype"] = package / "mimetype"
    archive = EXPORTS / f"{STEM}.epub"
    timestamp = tuple(datetime.fromisoformat(modified.replace("Z", "+00:00")).timetuple()[:6])
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as target:
        for relative in ["mimetype", *sorted(r for r in resources if r != "mimetype")]:
            info = zipfile.ZipInfo(relative, timestamp)
            info.compress_type = zipfile.ZIP_STORED if relative == "mimetype" else zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            target.writestr(info, resources[relative].read_bytes(), compresslevel=9)
    input_paths = [book_path, source_html, source_pdf, reading_manifest, plan_path, design_path, Path(__file__),
                   *[BOOK / p for p in book["chapters"]], *[BOOK / a["asset"] for a in plan["illustrations"]]]
    record = {"schema_version": 1, "edition": "illustrated-v3-epub", "format": "EPUB 3 fixed layout",
              "title": book["title"], "identifier": identifier, "modified_utc": modified,
              "story_pages": 30, "chapters": 6, "story_illustrations": 12,
              "library_cover": "Render of existing page 1, outside reading spine; no added story page",
              "viewport": [720,912], "spine": [f"EPUB/pages/page-{n:03d}.xhtml" for n in range(1,31)],
              "navigation": "Six chapters, thirty page targets and a start-reading landmark",
              "input_sha256": {str(p.relative_to(BOOK)):sha(p) for p in input_paths},
              "system_font_sha256": {name:sha(Path('/usr/share/fonts/truetype/noto')/name) for name in FONTS},
              "font_license_source": str(LICENSE), "font_license_sha256": sha(LICENSE),
              "package_sha256": {r:sha(p) for r,p in resources.items()},
              "epub_path": str(archive.relative_to(BOOK)), "epub_sha256": sha(archive),
              "size_bytes": archive.stat().st_size,
              "build": "python3 production/build_epub.py", "validation": "pending EPUBCheck and actual package proof",
              "sources": ["https://www.w3.org/TR/epub-33/#sec-fixed-layouts", "https://www.w3.org/publishing/epubcheck/"],
              "limits": "Actual reader application/device behavior needs its own test; no Apple Books/Kindle/device certification."}
    old_manifest.write_text(json.dumps(record, indent=2) + "\n")
    print(f"Built {archive}\n30 fixed-layout XHTML story pages;12 illustrations;3 embedded fonts;6 chapter links.")


if __name__ == "__main__":
    main()
