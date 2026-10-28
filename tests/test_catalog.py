"""Automated checks for the public library site.

Covers, for the real repository state:
  * manifest integrity (schema, ids, exact selected editions),
  * artifact integrity (sizes, sha256, PDF signature, actual EPUB package
    behavior including the uncompressed mimetype entry, package document,
    spine, dc:language and rendition:layout honest labeling),
  * build output correctness (complete catalog, relative project-subpath
    URLs only, no studio/process files leaked into the site),
  * pinned vendored reader libraries (sha256 recorded in PROVENANCE.md).

Failure-mode tests prove the checks actually reject bad inputs: absolute
links, remote URLs, damaged PDF/EPUB files, missing artifacts and bad ids.
Run with: python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import re
import shutil
import tempfile
import unittest
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / "publications"
SITE = ROOT / "site"
MODULE_PATH = ROOT / "tools" / "build_catalog.py"

spec = importlib.util.spec_from_file_location("build_catalog", MODULE_PATH)
bc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bc)

# The initial release set. Tests treat these as a *subset* so new editions can
# be added to the manifest without editing tests; everything else is derived
# from publications/manifest.json itself.
INITIAL_IDS = {
    "nell-and-the-pocket-sized-storm",
    "mila-and-the-missing-moon",
    "mila-y-la-luna-perdida",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_manifest(root: Path, books: list[dict]) -> None:
    (root / "publications").mkdir(parents=True, exist_ok=True)
    (root / "publications" / "manifest.json").write_text(
        json.dumps({"schema": 1, "books": books}), encoding="utf-8"
    )


def file_entry(path: Path, rel: str) -> dict:
    return {"path": rel, "bytes": path.stat().st_size, "sha256": sha256(path)}


def make_epub(path: Path, lang: str = "en", layout: str | None = None, title: str = "Test") -> None:
    opf_meta = f"<dc:language>{lang}</dc:language>"
    if layout:
        opf_meta += f"<meta property='rendition:layout'>{layout}</meta>"
    opf = (
        "<?xml version='1.0'?>"
        "<package xmlns='http://www.idpf.org/2007/opf' version='3.0'>"
        f"<metadata xmlns:dc='http://purl.org/dc/elements/1.1/'><dc:title>{title}</dc:title>{opf_meta}</metadata>"
        "<manifest><item id='nav' href='nav.xhtml' media-type='application/xhtml+xml' properties='nav'/>"
        "<item id='c1' href='c1.xhtml' media-type='application/xhtml+xml'/></manifest>"
        "<spine><itemref idref='c1'/></spine></package>"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr(
            "META-INF/container.xml",
            "<?xml version='1.0'?><container xmlns='urn:oasis:names:tc:opendocument:xmlns:container'>"
            "<rootfiles><rootfile full-path='package.opf' media-type='application/oebps-package+xml'/></rootfiles></container>",
        )
        z.writestr("package.opf", opf)
        z.writestr("nav.xhtml", "<html xmlns='http://www.w3.org/1999/xhtml'><body><nav></nav></body></html>")
        z.writestr("c1.xhtml", "<html xmlns='http://www.w3.org/1999/xhtml'><body>hello</body></html>")


def make_book_entry(book_id: str, epub_path: Path, pdf_path: Path, cover_path: Path | None = None,
                    lang: str = "en", layout: str = "reflowable") -> dict:
    entry = {
        "id": book_id,
        "title": f"Title {book_id}",
        "summary": f"Summary {book_id}",
        "language": lang,
        "layout": layout,
        "downloads": {"epub": file_entry(epub_path, epub_path.name)},
        "cover": {
            "path": f"covers/{cover_path.name}",
            "bytes": cover_path.stat().st_size,
            "sha256": sha256(cover_path),
        },
    }
    if pdf_path is not None:
        entry["downloads"]["pdf"] = file_entry(pdf_path, pdf_path.name)
    return entry


class RealRepoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = bc.load_manifest(PUB)
        cls.books = bc.validate_manifest(cls.manifest)

    def test_manifest_ids_are_the_selected_editions(self):
        ids = {b["id"] for b in self.books}
        self.assertTrue(ids, "manifest lists no books")
        # The initial release set must still be present; the catalog may grow
        # without test edits, but never lose a selected edition silently.
        self.assertTrue(INITIAL_IDS <= ids, f"missing selected editions: {INITIAL_IDS - ids}")

    def test_languages_and_layouts_are_labeled_honestly(self):
        for book in self.books:
            self.assertIn(book["language"], ("en", "es"), f"{book['id']}: unexpected language")
            self.assertIn(book["layout"], ("fixed", "reflowable"), f"{book['id']}: unexpected layout")
        by_id = {b["id"]: b for b in self.books}
        for book_id, lang, layout in (
            ("nell-and-the-pocket-sized-storm", "en", "fixed"),
            ("mila-and-the-missing-moon", "en", "reflowable"),
            ("mila-y-la-luna-perdida", "es", "reflowable"),
        ):
            if book_id in by_id:
                self.assertEqual(by_id[book_id]["language"], lang, book_id)
                self.assertEqual(by_id[book_id]["layout"], layout, book_id)

    def test_artifact_integrity(self):
        for book in self.books:
            bc.validate_artifact(PUB, book)

    def test_epub_package_behavior(self):
        for book in self.books:
            path = PUB / book["downloads"]["epub"]["path"]
            with zipfile.ZipFile(path) as z:
                names = z.namelist()
                self.assertEqual(names[0], "mimetype", f"{path.name}: mimetype must be the first entry")
                self.assertEqual(z.getinfo("mimetype").compress_type, zipfile.ZIP_STORED)
                self.assertEqual(z.read("mimetype"), b"application/epub+zip")
                self.assertIsNone(z.testzip(), f"{path.name}: corrupt archive entry")
                container = ET.fromstring(z.read("META-INF/container.xml"))
                opf_path = container.find(
                    ".//c:rootfile", {"c": "urn:oasis:names:tc:opendocument:xmlns:container"}
                ).get("full-path")
                opf = ET.fromstring(z.read(opf_path))
                metadata = opf.find("{*}metadata")
                langs = ["".join(e.itertext()).strip() for e in metadata.findall("{*}language")]
                self.assertIn(book["language"], langs, f"{path.name}: language labeling")
                layouts = [
                    "".join(m.itertext()).strip()
                    for m in metadata.findall("{*}meta")
                    if m.get("property") == "rendition:layout"
                ]
                actual = "fixed" if layouts == ["pre-paginated"] else "reflowable"
                self.assertEqual(actual, book["layout"], f"{path.name}: layout labeling")
                spine = opf.find("{*}spine")
                self.assertGreaterEqual(len(spine.findall("{*}itemref")), 1, f"{path.name}: empty spine")

    def test_covers_exist_and_match_manifest(self):
        for book in self.books:
            cover = PUB / book["cover"]["path"]
            self.assertTrue(cover.is_file(), f"missing cover {cover}")
            self.assertEqual(cover.stat().st_size, book["cover"]["bytes"])
            self.assertEqual(sha256(cover), book["cover"]["sha256"])
            self.assertIn(cover.read_bytes()[:3], (b"\xff\xd8\xff", b"\x89PNG"))

    def test_audiobook_page_and_chapters(self):
        page = (SITE / "audiobook.html").read_text(encoding="utf-8")
        self.assertEqual(page.count("<audio "), 22, "one chapter player per chapter")
        self.assertNotRegex(page, r"<audio[^>]*\bautoplay\b", "audio must not autoplay")
        self.assertIn('preload="none"', page)
        manifest = json.loads(
            (SITE / "audio" / "the-ledger-of-ashes" / "chapters.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["book_id"], "the-ledger-of-ashes")
        self.assertEqual(len(manifest["chapters"]), 22)
        self.assertIn("Drama 3", manifest["credit"])
        for chapter in manifest["chapters"]:
            path = SITE / "audio" / "the-ledger-of-ashes" / chapter["file"]
            self.assertTrue(path.is_file(), f"missing {path}")
            self.assertEqual(path.stat().st_size, chapter["bytes"])
            self.assertEqual(sha256(path), chapter["sha256"])

    def test_vendored_reader_libraries_pinned(self):
        provenance = (SITE / "assets" / "vendor" / "PROVENANCE.md").read_text(encoding="utf-8")
        section = provenance.split("## Integrity (sha256)", 1)[1]
        recorded = dict(
            line.split(":", 1) for line in section.strip().splitlines() if ":" in line and ".js" in line
        )
        self.assertEqual(set(recorded), {"epub.min.js", "jszip.min.js"}, "PROVENANCE.md checksum list")
        for name, digest in recorded.items():
            path = SITE / "assets" / "vendor" / name
            self.assertTrue(path.is_file(), f"missing vendored {name}")
            self.assertEqual(sha256(path), digest.strip(), f"vendored {name} changed without updating PROVENANCE.md")
        for lic in ("LICENSE-epubjs.txt", "LICENSE-jszip.txt"):
            self.assertGreater((SITE / "assets" / "vendor" / lic).stat().st_size, 500, f"missing license {lic}")

    def test_reader_loads_jszip_before_epubjs(self):
        html = (SITE / "reader.html").read_text(encoding="utf-8")
        self.assertLess(
            html.index("assets/vendor/jszip.min.js"),
            html.index("assets/vendor/epub.min.js"),
            "EPUB.js requires JSZip to be included first for archived .epub files",
        )


class BuildOutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="books-site-build-")
        cls.out = Path(cls.tmp) / "_site"
        cls.summary = bc.build(ROOT, cls.out)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_summary_counts(self):
        books = bc.validate_manifest(bc.load_manifest(PUB))
        expected_files = sum(len(b["downloads"]) + 1 for b in books)  # + cover
        self.assertEqual(self.summary["books"], len(books))
        self.assertEqual(self.summary["publication_files"], expected_files)

    def test_catalog_json_complete_and_public(self):
        manifest_ids = {b["id"] for b in bc.validate_manifest(bc.load_manifest(PUB))}
        catalog = json.loads((self.out / "catalog.json").read_text(encoding="utf-8"))
        self.assertEqual({b["id"] for b in catalog["books"]}, manifest_ids)
        for book in catalog["books"]:
            for url in list(book["downloads"].values()) + [book["cover"]]:
                self.assertTrue(url.startswith("publications/"), f"non-public path {url}")
                self.assertTrue((self.out / url).is_file(), f"missing {url}")
        text = (self.out / "catalog.json").read_text(encoding="utf-8")
        self.assertNotIn("sources", text, "studio source paths must not leak into the public catalog")
        self.assertNotIn("sha256", text)

    def test_only_relative_project_subpath_urls(self):
        for html in self.out.rglob("*.html"):
            for match in re.finditer(
                r"""(?:href|src)\s*=\s*["']([^"']*)["']""", html.read_text(encoding="utf-8"), re.I
            ):
                url = match.group(1)
                if url and not url.startswith(("#", "data:", "mailto:")):
                    self.assertFalse(url.startswith("/"), f"absolute URL in {html.name}: {url}")
                    self.assertIsNone(
                        re.match(r"^[a-z][a-z0-9+.-]*:", url, re.I), f"remote URL in {html.name}: {url}"
                    )

    def test_no_studio_or_process_files_in_output(self):
        names = {p.name for p in self.out.rglob("*") if p.is_file()}
        for forbidden in ("manifest.json", "AGENTS.md", "AGETNS.md", "tasks.json", "handoff.md"):
            self.assertNotIn(forbidden, names)
        self.assertFalse((self.out / ".studio").exists())

    def test_all_publication_artifacts_surfaced(self):
        html = "\n".join(p.read_text(encoding="utf-8") for p in self.out.rglob("*.html"))
        for book in json.loads((self.out / "catalog.json").read_text(encoding="utf-8"))["books"]:
            self.assertIn(f"reader.html?book={book['id']}", html)
            self.assertIn(book["cover"], html)
            for url in book["downloads"].values():
                self.assertIn(url, html)


class OutputSafetyTests(unittest.TestCase):
    """Sentinel tests: output cleanup must never delete source, ancestors,
    symlinks or unrelated existing directories. All cases run against
    temporary fixtures, never the real repository root."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="books-outsafety-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.root = self.tmp / "root"
        (self.root / "site").mkdir(parents=True)
        (self.root / "site" / "index.html").write_text(
            '<!doctype html><title>t</title>'
            '<a href="reader.html?book=book">Read</a>'
            '<a href="publications/book.epub">e</a>'
            '<a href="publications/book.pdf">p</a>'
            '<img src="publications/covers/cover.jpg" alt="">',
            encoding="utf-8",
        )
        (self.root / "site" / "reader.html").write_text(
            "<!doctype html><title>Reader</title>", encoding="utf-8"
        )
        pub = self.root / "publications"
        pub.mkdir()
        make_epub(pub / "book.epub", lang="en", layout="reflowable")
        (pub / "book.pdf").write_bytes(b"%PDF-1.7\nfake\n%%EOF\n")
        (pub / "covers").mkdir()
        (pub / "covers" / "cover.jpg").write_bytes(b"\xff\xd8\xff" + b"x" * 100)
        write_manifest(
            self.root,
            [make_book_entry("book", pub / "book.epub", pub / "book.pdf", pub / "covers" / "cover.jpg")],
        )

    def test_source_root_rejected(self):
        with self.assertRaises(bc.BuildError):
            bc.build(self.root, self.root)
        self.assertTrue((self.root / "site" / "index.html").is_file(), "source root was damaged")

    def test_ancestor_rejected(self):
        with self.assertRaises(bc.BuildError):
            bc.build(self.root, self.root.parent)
        self.assertTrue((self.root / "publications" / "manifest.json").is_file())

    def test_unrelated_populated_dir_preserved(self):
        precious = self.tmp / "precious"
        precious.mkdir()
        sentinel = precious / "keep-me.txt"
        sentinel.write_text("do not delete", encoding="utf-8")
        with self.assertRaises(bc.BuildError):
            bc.build(self.root, precious)
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "do not delete")

    def test_symlink_output_rejected(self):
        precious = self.tmp / "precious"
        precious.mkdir()
        (precious / "keep-me.txt").write_text("do not delete", encoding="utf-8")
        link = self.tmp / "link-to-precious"
        link.symlink_to(precious)
        with self.assertRaises(bc.BuildError):
            bc.build(self.root, link)
        self.assertTrue((precious / "keep-me.txt").is_file(), "symlink target was damaged")

    def test_rebuild_owned_output_twice(self):
        out = self.tmp / "out"
        first = bc.build(self.root, out)
        self.assertEqual(first["books"], 1)
        marker = out / bc.OUTPUT_MARKER
        self.assertTrue(marker.is_file(), "successful builds must mark the output as owned")
        second = bc.build(self.root, out)
        self.assertEqual(second["books"], 1)
        self.assertTrue((out / "catalog.json").is_file())
        self.assertTrue(marker.is_file())

    def test_legacy_default_site_replaced_once(self):
        legacy = self.root / "_site"
        legacy.mkdir()
        (legacy / "catalog.json").write_text("{}", encoding="utf-8")
        (legacy / "index.html").write_text("old build", encoding="utf-8")
        (legacy / "publications").mkdir()
        summary = bc.build(self.root, legacy)
        self.assertEqual(summary["books"], 1)
        self.assertTrue((legacy / bc.OUTPUT_MARKER).is_file())


class FailureModeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="books-buildcheck-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.root = self.tmp / "root"
        (self.root / "site").mkdir(parents=True)
        self.links_html = (
            '<!doctype html><title>t</title>'
            '<a href="reader.html?book=book">Read</a>'
            '<a href="publications/book.epub">e</a>'
            '<a href="publications/book.pdf">p</a>'
            '<img src="publications/covers/cover.jpg" alt="">'
        )
        (self.root / "site" / "index.html").write_text(self.links_html, encoding="utf-8")
        (self.root / "site" / "reader.html").write_text(
            "<!doctype html><title>Reader</title>", encoding="utf-8"
        )
        self.pub = self.root / "publications"
        self.pub.mkdir()
        make_epub(self.pub / "book.epub", lang="en", layout="reflowable")
        (self.pub / "book.pdf").write_bytes(b"%PDF-1.7\nfake\n%%EOF\n")
        (self.pub / "covers").mkdir()
        (self.pub / "covers" / "cover.jpg").write_bytes(b"\xff\xd8\xff" + b"x" * 100)
        self.entry = make_book_entry(
            "book", self.pub / "book.epub", self.pub / "book.pdf", self.pub / "covers" / "cover.jpg"
        )

    def expect_build_error(self, root=None):
        with self.assertRaises(bc.BuildError):
            bc.build(root or self.root, (self.tmp / "out"))

    def test_minimal_fixture_builds(self):
        write_manifest(self.root, [self.entry])
        out = self.tmp / "out-ok"
        summary = bc.build(self.root, out)
        self.assertEqual(summary["books"], 1)

    def test_absolute_link_fails(self):
        write_manifest(self.root, [self.entry])
        (self.root / "site" / "index.html").write_text(
            self.links_html + '<a href="/books/index.html">abs</a>', encoding="utf-8"
        )
        self.expect_build_error()

    def test_remote_cdn_url_fails(self):
        write_manifest(self.root, [self.entry])
        (self.root / "site" / "index.html").write_text(
            self.links_html + '<script src="https://cdn.example.com/x.js"></script>', encoding="utf-8"
        )
        self.expect_build_error()

    def test_broken_local_link_fails(self):
        write_manifest(self.root, [self.entry])
        (self.root / "site" / "index.html").write_text(
            self.links_html + '<img src="assets/missing.png" alt="">', encoding="utf-8"
        )
        self.expect_build_error()

    def test_pdf_signature_rejected(self):
        (self.pub / "book.pdf").write_bytes(b"not a pdf at all\n")
        write_manifest(self.root, [self.entry])
        self.expect_build_error()

    def test_epub_mimetype_rejected(self):
        with zipfile.ZipFile(self.pub / "book.epub", "w") as z:
            z.writestr("mimetype", "application/epub+zip")
            z.writestr("META-INF/container.xml", "<container/>")
        write_manifest(self.root, [self.entry])
        self.expect_build_error()

    def test_not_a_zip_rejected(self):
        (self.pub / "book.epub").write_bytes(b"plain text pretending\n")
        write_manifest(self.root, [self.entry])
        self.expect_build_error()

    def test_missing_artifact_fails(self):
        entry = make_book_entry(
            "book", self.pub / "book.epub", self.pub / "book.pdf", self.pub / "covers" / "cover.jpg"
        )
        entry["downloads"]["epub"]["path"] = "gone.epub"
        write_manifest(self.root, [entry])
        self.expect_build_error()

    def test_hash_mismatch_fails(self):
        (self.pub / "book.epub").write_bytes(self.pub.joinpath("book.epub").read_bytes() + b"\0")
        write_manifest(self.root, [self.entry])
        self.expect_build_error()

    def test_layout_dishonesty_rejected(self):
        # manifest claims fixed, the actual EPUB is reflowable
        entry = dict(self.entry)
        entry["layout"] = "fixed"
        write_manifest(self.root, [entry])
        self.expect_build_error()

    def test_language_dishonesty_rejected(self):
        entry = dict(self.entry)
        entry["language"] = "es"
        write_manifest(self.root, [entry])
        self.expect_build_error()

    def test_bad_id_rejected(self):
        entry = dict(self.entry)
        entry["id"] = "Bad_ID"
        write_manifest(self.root, [entry])
        self.expect_build_error()

    def test_duplicate_id_rejected(self):
        write_manifest(self.root, [self.entry, dict(self.entry)])
        self.expect_build_error()

    def test_unsurfaced_artifact_fails(self):
        write_manifest(self.root, [self.entry])
        # Build works, then check the surfaced rule: rebuild with a book whose
        # links are absent from index.html (cover never linked).
        (self.root / "site" / "index.html").write_text(
            '<a href="reader.html?book=book">Read</a><a href="publications/book.epub">e</a>'
            '<a href="publications/book.pdf">p</a>',
            encoding="utf-8",
        )
        out = self.tmp / "out2"
        with self.assertRaises(bc.BuildError) as ctx:
            bc.build(self.root, out)
        self.assertIn("cover", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()