#!/usr/bin/env python3
"""Build the public library website for GitHub Pages.

Assembles an isolated output directory (default: _site) from site/ and
publications/ only, after validating the publication manifest and the
actual artifact packages (PDF signatures, EPUB structure, hashes, sizes).

Subcommands:
  build             validate inputs, assemble the output, check all local links
  validate          run all validations without writing any output
  hash PATH         print sha256 and byte size of a file (helper for manifest.json)
  cover EPUB --id ID
                    extract the cover image from an EPUB into publications/covers/

The site is served under the /books/ project path on GitHub Pages, so every
generated or referenced URL must be relative; the build fails on absolute
paths and remote URLs.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import shutil
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_DIR_NAME = "site"
PUB_DIR_NAME = "publications"
PUB_URL_PREFIX = "publications/"
DEFAULT_OUTPUT = "_site"
OUTPUT_MARKER = ".generated-by-build_catalog"

ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
LINK_RE = re.compile(r"""(?:href|src)\s*=\s*["']([^"']*)["']""", re.I)
EPUB_MIMETYPE = b"application/epub+zip"
CONTAINER_PATH = "META-INF/container.xml"
CONTAINER_NS = {"c": "urn:oasis:names:tc:opendocument:xmlns:container"}

LANG_LABELS = {"en": "English", "es": "Español"}
LAYOUT_LABELS = {"fixed": "Fixed layout", "reflowable": "Reflowable"}


class BuildError(Exception):
    """Raised when validation or assembly must fail the build."""


def fail(msg: str):
    raise BuildError(msg)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_rel_path(value: str, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        fail(f"{what}: path must be a non-empty string")
    if Path(value).is_absolute():
        fail(f"{what}: path must be relative, got {value!r}")
    parts = [p for p in Path(value).parts if p not in ("", ".")]
    if ".." in parts:
        fail(f"{what}: path must stay inside publications/, got {value!r}")
    return "/".join(parts)


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------

def load_manifest(pub_dir: Path) -> dict:
    manifest_path = pub_dir / "manifest.json"
    if not manifest_path.is_file():
        fail(f"missing {manifest_path}")
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        fail(f"manifest.json is not valid JSON: {e}")
    if not isinstance(data, dict) or data.get("schema") != 1:
        fail("manifest.json: expected {\"schema\": 1, ...}")
    return data


def validate_manifest(data: dict) -> list[dict]:
    books = data.get("books")
    if not isinstance(books, list) or not books:
        fail("manifest.json: 'books' must be a non-empty list")
    seen: set[str] = set()
    for i, book in enumerate(books):
        where = f"books[{i}]"
        if not isinstance(book, dict):
            fail(f"{where}: must be an object")
        bid = book.get("id")
        if not isinstance(bid, str) or not ID_RE.match(bid):
            fail(f"{where}.id: expected a lowercase slug like 'mila-and-the-missing-moon', got {bid!r}")
        if bid in seen:
            fail(f"{where}.id: duplicate id {bid!r}")
        seen.add(bid)
        for field in ("title", "summary"):
            value = book.get(field)
            if not isinstance(value, str) or not value.strip():
                fail(f"{where}.{field}: must be a non-empty string")
        lang = book.get("language")
        if not isinstance(lang, str) or not re.match(r"^[a-z]{2,3}$", lang):
            fail(f"{where}.language: expected an ISO language code like 'en' or 'es', got {lang!r}")
        layout = book.get("layout")
        if layout not in ("fixed", "reflowable"):
            fail(f"{where}.layout: expected 'fixed' or 'reflowable', got {layout!r}")
        downloads = book.get("downloads")
        if not isinstance(downloads, dict) or "epub" not in downloads:
            fail(f"{where}.downloads: must be an object with at least an 'epub' entry")
        for kind, entry in downloads.items():
            if kind not in ("epub", "pdf"):
                fail(f"{where}.downloads: unexpected kind {kind!r}")
            if not isinstance(entry, dict):
                fail(f"{where}.downloads.{kind}: must be an object")
            safe_rel_path(entry.get("path", ""), f"{where}.downloads.{kind}")
            if not isinstance(entry.get("bytes"), int) or entry["bytes"] < 0:
                fail(f"{where}.downloads.{kind}.bytes: expected a non-negative integer")
            sha = entry.get("sha256")
            if not isinstance(sha, str) or not SHA_RE.match(sha):
                fail(f"{where}.downloads.{kind}.sha256: expected a 64-character hex digest")
        cover = book.get("cover")
        if not isinstance(cover, dict):
            fail(f"{where}.cover: must be an object")
        safe_rel_path(cover.get("path", ""), f"{where}.cover.path")
        if not isinstance(cover.get("bytes"), int) or cover["bytes"] < 0:
            fail(f"{where}.cover.bytes: expected a non-negative integer")
        if not isinstance(cover.get("sha256"), str) or not SHA_RE.match(cover["sha256"]):
            fail(f"{where}.cover.sha256: expected a 64-character hex digest")
    return books


# ---------------------------------------------------------------------------
# Artifact checks
# ---------------------------------------------------------------------------

def check_pdf(path: Path) -> None:
    with path.open("rb") as f:
        head = f.read(8)
    if head[:5] != b"%PDF-":
        fail(f"{path.name}: not a PDF (missing %PDF- header)")
    with path.open("rb") as f:
        f.seek(max(0, path.stat().st_size - 2048))
        tail = f.read()
    if b"%%EOF" not in tail:
        fail(f"{path.name}: PDF is truncated or missing its end marker")


def epub_opf(zf: zipfile.ZipFile) -> tuple[str, ET.Element, str]:
    names = zf.namelist()
    if not names or names[0] != "mimetype":
        fail("EPUB: first archive entry must be the uncompressed 'mimetype' file")
    info = zf.getinfo("mimetype")
    if info.compress_type != zipfile.ZIP_STORED:
        fail("EPUB: 'mimetype' entry must be stored uncompressed")
    if zf.read("mimetype") != EPUB_MIMETYPE:
        fail(f"EPUB: 'mimetype' content must be {EPUB_MIMETYPE.decode()}")
    if CONTAINER_PATH not in names:
        fail(f"EPUB: missing {CONTAINER_PATH}")
    try:
        container = ET.fromstring(zf.read(CONTAINER_PATH))
        rootfile = container.find(".//c:rootfile", CONTAINER_NS)
        opf_path = rootfile.get("full-path")
        opf = ET.fromstring(zf.read(opf_path))
    except (ET.ParseError, AttributeError, KeyError) as e:
        fail(f"EPUB: cannot parse package document ({e})")
    return opf_path, opf, "/".join(opf_path.split("/")[:-1])


def check_epub(path: Path, expect_lang: str | None = None, expect_layout: str | None = None) -> None:
    if not zipfile.is_zipfile(path):
        fail(f"{path.name}: not a valid EPUB (not a zip archive)")
    with zipfile.ZipFile(path) as z:
        if z.testzip() is not None:
            fail(f"{path.name}: EPUB archive contains corrupted entries")
        _opf_path, opf, _base = epub_opf(z)
        metadata = opf.find("{*}metadata")
        if metadata is None:
            fail(f"{path.name}: EPUB package document has no metadata element")
        languages = ["".join(e.itertext()).strip() for e in metadata.findall("{*}language")]
        if expect_lang is not None and expect_lang not in languages:
            fail(f"{path.name}: EPUB dc:language {languages} does not match manifest language {expect_lang!r}")
        layout = None
        for meta in metadata.findall("{*}meta"):
            if meta.get("property") == "rendition:layout":
                layout = "".join(meta.itertext()).strip()
        if layout == "pre-paginated":
            actual = "fixed"
        elif layout in (None, "", "reflowable"):
            actual = "reflowable"
        else:
            actual = layout
        if expect_layout is not None and actual != expect_layout:
            fail(f"{path.name}: EPUB rendition:layout {layout!r} does not match manifest layout {expect_layout!r}")
        spine = opf.find("{*}spine")
        if spine is None or len(spine.findall("{*}itemref")) < 1:
            fail(f"{path.name}: EPUB spine is empty")


def validate_artifact(pub_dir: Path, book: dict) -> None:
    where = f"book {book['id']}"
    entries = [("epub", book["downloads"]["epub"]), ("pdf", book["downloads"].get("pdf"))]
    entries.append(("cover", book["cover"]))
    for kind, entry in entries:
        if entry is None:
            continue
        path = pub_dir / safe_rel_path(entry["path"], f"{where} {kind}")
        if not path.is_file():
            fail(f"{where}: selected {kind} file is missing: publications/{entry['path']}")
        size = path.stat().st_size
        if size != entry["bytes"]:
            fail(f"{where}: {kind} size {size} does not match manifest bytes {entry['bytes']}")
        digest = sha256_file(path)
        if digest != entry["sha256"]:
            fail(f"{where}: {kind} sha256 {digest} does not match manifest")
        if kind == "epub":
            check_epub(path, expect_lang=book["language"], expect_layout=book["layout"])
        elif kind == "pdf":
            check_pdf(path)
        else:
            with path.open("rb") as f:
                head = f.read(3)
            if head not in (b"\xff\xd8\xff", b"\x89PNG"):
                fail(f"{where}: cover is neither a JPEG nor a PNG")


def validate_all(root: Path) -> list[dict]:
    pub_dir = root / PUB_DIR_NAME
    site_dir = root / SITE_DIR_NAME
    if not site_dir.is_dir():
        fail(f"missing {site_dir} (the website sources)")
    books = validate_manifest(load_manifest(pub_dir))
    for book in books:
        validate_artifact(pub_dir, book)
    return books


# ---------------------------------------------------------------------------
# Public catalog projection
# ---------------------------------------------------------------------------

def public_catalog(books: list[dict]) -> dict:
    out_books = []
    for book in books:
        out_books.append({
            "id": book["id"],
            "title": book["title"],
            "summary": book["summary"],
            "language": book["language"],
            "language_label": LANG_LABELS.get(book["language"], book["language"].upper()),
            "layout": book["layout"],
            "layout_label": LAYOUT_LABELS[book["layout"]],
            "downloads": {
                kind: PUB_URL_PREFIX + entry["path"]
                for kind, entry in book["downloads"].items()
            },
            "cover": PUB_URL_PREFIX + book["cover"]["path"],
            "sizes": {
                kind: entry["bytes"] for kind, entry in book["downloads"].items()
            },
        })
    return {"schema": 1, "books": out_books}


# ---------------------------------------------------------------------------
# Output assembly and link checks
# ---------------------------------------------------------------------------

def check_links(out_dir: Path, catalog: dict) -> None:
    problems: list[str] = []
    html_files = sorted(out_dir.rglob("*.html"))
    if not html_files:
        fail("build output contains no HTML pages")

    referenced = set()
    for html in html_files:
        text = html.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(text):
            url = match.group(1)
            if url in ("",) or url.startswith("#") or url.startswith("data:") or url.startswith("mailto:"):
                continue
            if url.startswith("/"):
                problems.append(f"{html.relative_to(out_dir)}: absolute URL breaks the /books/ project path: {url!r}")
                continue
            if re.match(r"^[a-z][a-z0-9+.-]*:", url, re.I):
                problems.append(f"{html.relative_to(out_dir)}: remote URLs are not allowed in the build: {url!r}")
                continue
            local = url.split("#", 1)[0].split("?", 1)[0]
            if not local:
                continue
            target = (html.parent / local).resolve()
            if not target.exists():
                problems.append(f"{html.relative_to(out_dir)}: broken local link: {url!r}")
            referenced.add(str(Path(url)))
    # catalog.json targets must exist and be relative
    for i, book in enumerate(catalog["books"]):
        for kind, url in book["downloads"].items():
            if not url.startswith(PUB_URL_PREFIX) or url.startswith("/") or ":" in url:
                problems.append(f"catalog.json books[{i}].downloads.{kind} must be a relative {PUB_URL_PREFIX}* URL, got {url!r}")
            elif not (out_dir / url).is_file():
                problems.append(f"catalog.json books[{i}].downloads.{kind}: missing file {url}")
        url = book["cover"]
        if not url.startswith(PUB_URL_PREFIX) or url.startswith("/") or ":" in url:
            problems.append(f"catalog.json books[{i}].cover must be a relative {PUB_URL_PREFIX}* URL, got {url!r}")
        elif not (out_dir / url).is_file():
            problems.append(f"catalog.json books[{i}].cover: missing file {url}")
    if problems:
        fail("link check failed:\n  " + "\n  ".join(problems))

    # Every selected artifact and every reader entry point must actually be surfaced.
    all_html = "\n".join(h.read_text(encoding="utf-8") for h in html_files)
    for book in catalog["books"]:
        for url in list(book["downloads"].values()) + [book["cover"]]:
            if url not in all_html:
                fail(f"book {book['id']}: {url} is published but not linked from any page")
        if f"reader.html?book={book['id']}" not in all_html:
            fail(f"book {book['id']}: no 'Read online' link (reader.html?book={book['id']}) found on any page")

    # No card may point the reader at a book the manifest does not list.
    valid_ids = {book["id"] for book in catalog["books"]}
    referenced_ids = set(re.findall(r"reader\.html\?book=([a-zA-Z0-9_-]+)", all_html))
    unknown = sorted(referenced_ids - valid_ids)
    if unknown:
        fail(
            "link check failed:\n  reader links reference book ids missing from the manifest: "
            + ", ".join(repr(i) for i in unknown)
        )


def _is_owned_output(root: Path, out: Path) -> bool:
    """True if an existing output directory was generated by this tool.

    A directory may be replaced only when it is empty, carries the build
    marker, or is a legacy default-named ``_site`` that visibly resembles
    output from an earlier build (catalog.json present and every top-level
    entry matches the site sources, the copied publications/ subtree, the
    catalog projection, or the marker). Anything else is someone else's
    directory and must never be deleted.
    """
    if out.is_symlink():
        fail(f"output path {out} is a symlink; refusing to write through it")
    if not out.exists():
        return True
    if not out.is_dir():
        fail(f"output path {out} exists and is not a directory")
    entries = list(out.iterdir())
    if not entries:
        return True
    if (out / OUTPUT_MARKER).is_file():
        return True
    if out.name == DEFAULT_OUTPUT:
        allowed_top = {p.name for p in (root / SITE_DIR_NAME).iterdir()} | {
            "catalog.json", PUB_DIR_NAME, OUTPUT_MARKER,
        }
        names = {e.name for e in entries}
        if "catalog.json" in names and names <= allowed_top:
            return True
    return False


def build(root: Path, out: Path) -> dict:
    books = validate_all(root)
    catalog = public_catalog(books)

    root_resolved = root.resolve()
    out_resolved = out.resolve()
    if out_resolved == root_resolved or out_resolved in root_resolved.parents:
        fail(f"output directory {out} must not be the source root or one of its ancestors")
    for guarded in (root / SITE_DIR_NAME, root / PUB_DIR_NAME):
        if out_resolved == guarded.resolve() or guarded.resolve() in out_resolved.parents:
            fail(f"output directory {out} must not contain {guarded}")
    if out.exists() and not _is_owned_output(root, out):
        fail(
            f"refusing to delete {out}: it already exists and is not recognized as "
            f"generated output (empty directory, {OUTPUT_MARKER} marker, or a legacy "
            f"{DEFAULT_OUTPUT}/ build). Choose a dedicated output directory."
        )
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(root / SITE_DIR_NAME, out)
    (out / OUTPUT_MARKER).write_text(
        "Generated by tools/build_catalog.py from site/ and publications/. Do not edit.\n",
        encoding="utf-8",
    )
    (out / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    pub_dir = root / PUB_DIR_NAME
    copied = 0
    bytes_copied = 0
    for book in books:
        entries = list(book["downloads"].values()) + [book["cover"]]
        for entry in entries:
            rel = safe_rel_path(entry["path"], f"book {book['id']}")
            src = pub_dir / rel
            dst = out / PUB_DIR_NAME / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
            copied += 1
            bytes_copied += src.stat().st_size

    check_links(out, catalog)

    return {
        "books": len(books),
        "publication_files": copied,
        "publication_bytes": bytes_copied,
        "output": str(out),
    }


# ---------------------------------------------------------------------------
# Cover extraction helper
# ---------------------------------------------------------------------------

def extract_cover(epub_path: Path, book_id: str, pub_dir: Path, max_width: int = 720) -> None:
    with zipfile.ZipFile(epub_path) as z:
        _opf_path, opf, base = epub_opf(z)
        manifest = opf.find("{*}manifest")
        if manifest is None:
            fail(f"{epub_path}: EPUB has no manifest element")
        items = {i.get("id"): i for i in manifest.findall("{*}item")}
        cover_item = None
        for it in items.values():
            if "cover-image" in (it.get("properties") or ""):
                cover_item = it
                break
        if cover_item is None:
            for meta in opf.find("{*}metadata").findall("{*}meta"):
                if meta.get("name") == "cover":
                    cover_item = items.get(meta.get("content"))
                    break
        if cover_item is None:
            cover_item = items.get("cover") or items.get("cover-image")
        if cover_item is None or not (cover_item.get("media-type") or "").startswith("image/"):
            fail(f"{epub_path}: no cover image found in the EPUB package")

        def norm(p: str) -> str:
            parts: list[str] = []
            for seg in (base + "/" + p).split("/"):
                if seg in ("", "."):
                    continue
                if seg == "..":
                    if parts:
                        parts.pop()
                    continue
                parts.append(seg)
            return "/".join(parts)

        image_path = norm(cover_item.get("href"))
        data = z.read(image_path)
    try:
        from PIL import Image
    except ImportError:
        out = pub_dir / "covers" / f"{book_id}{Path(image_path).suffix}"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
        print(f"wrote {out} ({len(data)} bytes, original bytes)")
        return
    im = Image.open(io.BytesIO(data))
    if im.mode != "RGB":
        bg = Image.new("RGB", im.size, (255, 252, 245))
        rgba = im.convert("RGBA")
        bg.paste(rgba, mask=rgba.split()[-1])
        im = bg
    if im.width > max_width:
        im = im.resize((max_width, round(im.height * max_width / im.width)), Image.LANCZOS)
    out = pub_dir / "covers" / f"{book_id}.jpg"
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, "JPEG", quality=85)
    print(f"wrote {out} ({out.stat().st_size} bytes, from {image_path})")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command")

    p_build = sub.add_parser("build", help="validate inputs and assemble the site output")
    p_build.add_argument("--output", default=DEFAULT_OUTPUT, help="output directory (default: _site)")

    sub.add_parser("validate", help="run all validations without building")

    p_hash = sub.add_parser("hash", help="print sha256 and size of a file")
    p_hash.add_argument("path")

    p_cover = sub.add_parser("cover", help="extract the cover image from an EPUB into publications/covers/")
    p_cover.add_argument("epub")
    p_cover.add_argument("--id", required=True)

    args = parser.parse_args(argv)
    if args.command is None:
        # Bare `python3 tools/build_catalog.py` means `build` into the default output.
        args.command = "build"
        args.output = DEFAULT_OUTPUT
    command = args.command
    try:
        if command == "build":
            out = Path(args.output)
            if not out.is_absolute():
                out = ROOT / out
            summary = build(ROOT, out)
            print(f"Built {summary['books']} book(s) into {summary['output']}")
            print(f"Copied {summary['publication_files']} publication files ({summary['publication_bytes']} bytes)")
            print("All manifest, package, hash and link checks passed.")
            return 0
        if command == "validate":
            books = validate_all(ROOT)
            print(f"Manifest valid: {len(books)} book(s); all artifact, package and hash checks passed.")
            return 0
        if command == "hash":
            path = Path(args.path)
            if not path.is_file():
                fail(f"no such file: {path}")
            print(f"path: {path}")
            print(f"bytes: {path.stat().st_size}")
            print(f"sha256: {sha256_file(path)}")
            return 0
        if command == "cover":
            extract_cover(Path(args.epub), args.id, ROOT / PUB_DIR_NAME)
            return 0
    except BuildError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())