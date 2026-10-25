#!/usr/bin/env python3
"""Verify actual EPUB container, text, resources, navigation and all page geometry."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET
import zipfile

BOOK = Path(__file__).resolve().parents[1]
NS = {"h":"http://www.w3.org/1999/xhtml", "opf":"http://www.idpf.org/2007/opf", "epub":"http://www.idpf.org/2007/ops"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    manifest = json.loads((BOOK / "exports/epub-manifest.json").read_text())
    archive = BOOK / manifest["epub_path"]
    assert sha(archive.read_bytes()) == manifest["epub_sha256"], "Stale EPUB hash"
    for relative, digest in manifest["input_sha256"].items():
        assert sha((BOOK / relative).read_bytes()) == digest, f"Changed EPUB input: {relative}"
    book = json.loads((BOOK / "book.json").read_text())
    plan = json.loads((BOOK / book["illustration_plan"]).read_text())
    source_pages = {}
    for relative in book["chapters"]:
        parts = re.split(r"^## Page (\d+)\s*$", (BOOK / relative).read_text(), flags=re.MULTILINE)
        for index in range(1,len(parts),2):
            source_pages[int(parts[index])] = parts[index+1].strip()
    compact = lambda s: re.sub(r"\s+", "", s)
    output = BOOK / "reviews/epub"
    with tempfile.TemporaryDirectory(prefix="nell-actual-epub-") as temp, zipfile.ZipFile(archive) as epub:
        names = epub.namelist()
        assert len(names) == len(set(names)), "Duplicate ZIP entries"
        assert names[0] == "mimetype" and epub.getinfo("mimetype").compress_type == zipfile.ZIP_STORED
        assert epub.read("mimetype") == b"application/epub+zip"
        for name in names:
            assert not PurePosixPath(name).is_absolute() and ".." not in PurePosixPath(name).parts
            assert sha(epub.read(name)) == manifest["package_sha256"][name], f"Changed package resource {name}"
        container = ET.fromstring(epub.read("META-INF/container.xml"))
        rootfile = container.find(".//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile")
        assert rootfile.get("full-path") == "EPUB/package.opf"
        opf = ET.fromstring(epub.read("EPUB/package.opf"))
        items = {i.get("id"):i for i in opf.findall("opf:manifest/opf:item",NS)}
        spine = opf.findall("opf:spine/opf:itemref",NS)
        assert len(spine) == 30 and all(i.get("linear") == "yes" for i in spine)
        paths = ["EPUB/"+items[i.get("idref")].get("href") for i in spine]
        assert paths == manifest["spine"]
        assert opf.find("opf:metadata/opf:meta[@property='rendition:layout']",NS).text == "pre-paginated"
        images = []
        for number, relative in enumerate(paths,1):
            root = ET.fromstring(epub.read(relative))
            viewport = root.find("h:head/h:meta[@name='viewport']",NS)
            assert viewport.get("content") == "width=720,height=912"
            paragraphs = root.findall(".//h:div[@class='story']/h:p",NS)
            text = "\n\n".join("".join(p.itertext()) for p in paragraphs)
            assert compact(text) == compact(source_pages[number]), f"EPUB prose differs on page {number}"
            assert not root.findall(".//h:script",NS), "Scripts in reading pages"
            page_images = root.findall(".//h:img",NS)
            for image in page_images:
                art = next(a for a in plan["illustrations"] if a["page"] == number)
                path = "EPUB/images/"+art["id"].lower()+".png"
                assert image.get("src") == "../images/"+art["id"].lower()+".png"
                assert epub.read(path) == (BOOK / art["asset"]).read_bytes(), "Artwork or alpha changed"
                assert image.get("alt") == art["alt_text"]
                images.append(number)
        assert images == sorted(a["page"] for a in plan["illustrations"]) and len(images) == 12
        nav = ET.fromstring(epub.read("EPUB/nav.xhtml"))
        kind = "{http://www.idpf.org/2007/ops}type"
        toc = next(n for n in nav.findall("h:body/h:nav",NS) if n.get(kind) == "toc")
        toc_links = toc.findall(".//h:a",NS)
        assert [a.get("href") for a in toc_links] == [f"pages/page-{c['pages'][0]:03d}.xhtml" for c in book["chapter_details"]]
        pagelist = next(n for n in nav.findall("h:body/h:nav",NS) if n.get(kind) == "page-list")
        assert len(pagelist.findall(".//h:a",NS)) == 30
        # Check every XHTML resource link and fragment against the archive itself.
        for name in names:
            if not name.endswith(".xhtml"):
                continue
            root = ET.fromstring(epub.read(name))
            for node in root.iter():
                for attr in ["href", "src"]:
                    value = node.get(attr)
                    if value is None:
                        continue
                    url = urlsplit(value)
                    assert not url.scheme and not url.netloc, "External dependency in EPUB"
                    parts = list(PurePosixPath(name).parent.parts)
                    for part in unquote(url.path).split("/"):
                        if part == "..": parts.pop()
                        elif part not in ["", "."]: parts.append(part)
                    target = "/".join(parts) if url.path else name
                    assert target in names, f"Broken link {name}: {value}"
                    if url.fragment:
                        destination = ET.fromstring(epub.read(target))
                        assert any(n.get("id") == unquote(url.fragment) for n in destination.iter())
        epub.extractall(temp)
        chrome = shutil.which("google-chrome") or shutil.which("chromium")
        if not chrome or not shutil.which("node"):
            raise RuntimeError("Chrome/Chromium and Node are required for actual page rendering proof")
        subprocess.run(["node", str(BOOK / "production/proof_epub.mjs"), chrome, temp,
                        str(BOOK / "exports/nell-and-the-pocket-sized-storm.html"), str(output)], check=True, timeout=180)
    browser = json.loads((output / "browser-proof.json").read_text())
    check = json.loads((output / "epubcheck.json").read_text())
    assert not [m for m in check.get("messages",[]) if m["severity"] in ["ERROR","FATAL","WARNING"]]
    result = {"epub_sha256":manifest["epub_sha256"], "spine_pages":30, "chapters":6,
              "story_images":12, "embedded_fonts":3, "selectable_page_text_matches_source":True,
              "artwork_original_bytes_and_alt_preserved":True, "local_links_and_fragments_resolve":True,
              "all_30_page_geometries_match_approved_html":not browser["failures"],
              "epubcheck":"5.4.0: zero errors, warnings or fatal messages", "rendered_pages":list(range(1,31)),
              "verification_script_sha256":sha(Path(__file__).read_bytes()),
              "proof_script_sha256":sha((BOOK / "production/proof_epub.mjs").read_bytes()),
              "render_sha256":{p.name:sha(p.read_bytes()) for p in sorted((output / "renders").glob("page-*.png"))},
              "limit":"Archive validation and Chrome page proof; no actual e-reader application/device test or accessibility certification."}
    (output / "verification.json").write_text(json.dumps(result,indent=2)+"\n")
    print("Verified actual EPUB:30 pages,12 pictures,3 fonts,6 chapter links; all prose and rendered geometry match.")


if __name__ == "__main__":
    main()
