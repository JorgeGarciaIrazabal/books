#!/usr/bin/env python3
"""Narration layer tool: pack raw page audio and validate what would ship.

The narration layer is separate from the book. ``production/narration/`` holds
the tagged script, the cast and the render record; ``narration/`` holds the
public per-page audio and the manifests the web reader consumes. Nothing here
writes into the manuscript, the export, the EPUB or the PDF, and ``validate``
fails if a performance tag is found in any of them.

Subcommands:
  pack      encode page WAVs to mono MP3, hash them, write narration/<id>/narration.json
            and update narration/manifest.json
  validate  check the public narration packages, the script/export agreement,
            and that published EPUB/PDF files contain no performance tags
  hash PATH print sha256 and byte size (helper for hand-written manifests)

Examples:
  python3 tools/narration.py pack \\
      --book-dir little-weather/standalone/nell-and-the-pocket-sized-storm \\
      --audio little-weather/standalone/nell-and-the-pocket-sized-storm/exports/narration-v1 \\
      --book-id nell-and-the-pocket-sized-storm
  python3 tools/narration.py validate
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NARRATION_DIR = "narration"
PUB_DIR = "publications"

TAG_PATTERNS = [
    re.compile(r"<\|speaker:\d+\|>"),
    re.compile(r"<\|(?:im_start|im_end|voice|text|interleave|semantic)[^>]*\|>"),
    re.compile(r"<\|speaker[^>]*\|>"),
    re.compile(r"</?(?:whisper|emphasis|soft|fast|slow|stress|forceful)>"),
]


class NarrationError(Exception):
    pass


def fail(message: str) -> None:
    raise NarrationError(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def duration_seconds(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=True)
    return round(float(result.stdout.strip()), 3)


def tags_in(text: str) -> list[str]:
    found: list[str] = []
    for pattern in TAG_PATTERNS:
        found.extend(match.group(0) for match in pattern.finditer(text))
    return found


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def load_json(path: Path, what: str) -> dict:
    if not path.is_file():
        fail(f"{what}: missing {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        fail(f"{what}: invalid JSON in {path}: {err}")


def safe_rel(value: str, what: str) -> str:
    if not value or value.startswith("/") or ".." in Path(value).parts or "\\" in value:
        fail(f"{what}: unsafe relative path {value!r}")
    return value


def load_publications(root: Path) -> dict[str, dict]:
    manifest_path = root / PUB_DIR / "manifest.json"
    if not manifest_path.is_file():
        return {}
    data = load_json(manifest_path, "publications manifest")
    return {book["id"]: book for book in data.get("books", [])}


def validate_package(root: Path, entry: dict, books: dict[str, dict]) -> dict:
    book_id = entry.get("id")
    if not isinstance(book_id, str) or book_id not in books:
        fail(f"narration: unknown book id {book_id!r}")
    book = books[book_id]
    if book.get("layout") != "fixed":
        fail(f"narration {book_id}: page audio requires a fixed-layout book")
    directory = safe_rel(entry.get("directory") or book_id, f"narration {book_id} directory")
    package = root / NARRATION_DIR / directory
    if not package.is_dir():
        fail(f"narration {book_id}: missing directory {package}")
    pages = entry.get("pages")
    files = entry.get("files")
    if not isinstance(pages, int) or pages < 1:
        fail(f"narration {book_id}: 'pages' must be a positive integer")
    if not isinstance(files, list) or len(files) != pages:
        fail(f"narration {book_id}: 'files' must list one file per page")
    seconds = entry.get("seconds")
    if not isinstance(seconds, (int, float)) or seconds <= 0:
        fail(f"narration {book_id}: 'seconds' must be positive")
    if not str(entry.get("credit") or "").strip():
        fail(f"narration {book_id}: a voice credit is required")
    seen = set()
    total = 0.0
    for item in files:
        page = item.get("page")
        if not isinstance(page, int) or page < 1 or page > pages or page in seen:
            fail(f"narration {book_id}: bad page number {page!r}")
        seen.add(page)
        rel = safe_rel(item.get("path") or "", f"narration {book_id} page {page}")
        path = package / rel
        if not path.is_file():
            fail(f"narration {book_id}: missing audio file {path}")
        if path.stat().st_size != item.get("bytes"):
            fail(f"narration {book_id}: page {page} size does not match the manifest")
        if sha256_file(path) != item.get("sha256"):
            fail(f"narration {book_id}: page {page} hash does not match the manifest")
        page_seconds = item.get("seconds")
        if not isinstance(page_seconds, (int, float)) or page_seconds <= 0:
            fail(f"narration {book_id}: page {page} needs a positive duration")
        total += float(page_seconds)
    if seen != set(range(1, pages + 1)):
        fail(f"narration {book_id}: page files are not contiguous 1..{pages}")
    if abs(total - float(seconds)) > max(1.0, pages * 0.15):
        fail(f"narration {book_id}: total duration {total:.1f}s disagrees with 'seconds' {seconds}")

    reader_manifest = package / "narration.json"
    reader = load_json(reader_manifest, f"narration {book_id} reader manifest")
    if reader.get("book") != book_id or reader.get("pages") != pages:
        fail(f"narration {book_id}: narration.json does not match the index entry")
    if reader.get("credit") != entry.get("credit"):
        fail(f"narration {book_id}: narration.json credit differs from the index")
    for item in reader.get("files", []):
        if not (package / safe_rel(item.get("src") or "", "narration src")).is_file():
            fail(f"narration {book_id}: narration.json points at a missing file")
    return entry


def validate_public(root: Path) -> dict:
    books = load_publications(root)
    index_path = root / NARRATION_DIR / "manifest.json"
    if not index_path.is_file():
        return {"books": 0, "files": 0}
    index = load_json(index_path, "narration manifest")
    entries = index.get("books")
    if not isinstance(entries, list):
        fail("narration manifest: 'books' must be a list")
    seen = set()
    for entry in entries:
        validate_package(root, entry, books)
        if entry["id"] in seen:
            fail(f"narration manifest: duplicate book id {entry['id']}")
        seen.add(entry["id"])
    return {"books": len(entries),
            "files": sum(len(entry["files"]) for entry in entries)}


def validate_book_sources(root: Path) -> list[str]:
    """Check each book that declares narration: script words and tag exclusion."""
    checked = []
    for book_json in sorted(root.glob("*/*/*/book.json")) + sorted(root.glob("*/*/*/*/book.json")):
        try:
            book = json.loads(book_json.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        narration = book.get("narration")
        if not isinstance(narration, dict):
            continue
        book_dir = book_json.parent
        script = book_dir / safe_rel(narration.get("script", ""), "narration script")
        source = book_dir / safe_rel(narration.get("source", ""), "narration source")
        builder = book_dir / "production/narration/tools/build_script_pages.py"
        if not script.is_file():
            fail(f"{book_dir.name}: narration script is missing ({script})")
        if not source.is_file():
            fail(f"{book_dir.name}: narration source is missing ({source})")
        if not builder.is_file():
            fail(f"{book_dir.name}: narration builder is missing ({builder})")
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pages.json"
            result = subprocess.run(
                [sys.executable, str(builder), str(script), str(source), str(out)],
                capture_output=True, text=True)
            if result.returncode != 0:
                fail(f"{book_dir.name}: narration script/export mismatch:\n{result.stderr.strip()}")

        # The story files themselves must never carry performance tags.
        story_files = sorted((book_dir / "manuscript").glob("*.md"))
        story_files += [source]
        for path in story_files:
            hits = tags_in(path.read_text(encoding="utf-8"))
            if hits:
                fail(f"{book_dir.name}: performance tag(s) in story file {path}: {hits[:3]}")
        checked.append(book_dir.name)
    return checked


def validate_publications_for_tags(root: Path) -> dict:
    """No published EPUB or PDF may contain a performance tag."""
    books = load_publications(root)
    scanned = {"epub": 0, "pdf": 0}
    pub_dir = root / PUB_DIR
    for book in books.values():
        for kind, entry in (book.get("downloads") or {}).items():
            path = pub_dir / entry["path"]
            if kind == "epub":
                with zipfile.ZipFile(path) as archive:
                    for name in archive.namelist():
                        if name.endswith((".xhtml", ".html", ".htm")):
                            hits = tags_in(archive.read(name).decode("utf-8", "replace"))
                            if hits:
                                fail(f"{path.name}: performance tag(s) inside {name}: {hits[:3]}")
                scanned["epub"] += 1
            elif kind == "pdf" and shutil.which("pdftotext"):
                text = subprocess.run(["pdftotext", "-layout", str(path), "-"],
                                      capture_output=True, text=True).stdout
                hits = tags_in(text)
                if hits:
                    fail(f"{path.name}: performance tag(s) in PDF text: {hits[:3]}")
                scanned["pdf"] += 1
    return scanned


def validate(root: Path) -> dict:
    public = validate_public(root)
    books = validate_book_sources(root)
    scanned = validate_publications_for_tags(root)
    return {"narration_books": public["books"], "narration_files": public["files"],
            "declared_books": books, "scanned": scanned}


# ---------------------------------------------------------------------------
# Packing
# ---------------------------------------------------------------------------

def read_cast(book_dir: Path) -> dict:
    path = book_dir / "production/narration/cast.json"
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def encode_mp3(wav: Path, out: Path, bitrate: str) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(wav),
         "-ac", "1", "-ar", "44100", "-c:a", "libmp3lame", "-b:a", bitrate,
         str(out)],
        capture_output=True, text=True)
    if result.returncode != 0:
        fail(f"ffmpeg failed for {wav.name}: {result.stderr.strip()[:300]}")


def pack(root: Path, book_dir: Path, audio: Path, book_id: str, bitrate: str,
         credit: str | None) -> dict:
    if not book_dir.is_dir():
        fail(f"pack: missing book directory {book_dir}")
    if not audio.is_dir():
        fail(f"pack: missing audio directory {audio}")
    wavs = sorted(audio.glob("page-*.wav"))
    if not wavs:
        fail(f"pack: no page-*.wav in {audio}")
    pages = []
    expected = 1
    for wav in wavs:
        match = re.fullmatch(r"page-(\d+)\.wav", wav.name)
        if not match or wav.parent != audio:
            continue
        number = int(match.group(1))
        if number != expected:
            fail(f"pack: page sequence broken at {wav.name}; expected page-{expected:02d}")
        expected += 1
        pages.append((number, wav))
    if [number for number, _ in pages] != list(range(1, len(pages) + 1)):
        fail("pack: pages must run 1..N")

    cast = read_cast(book_dir)
    voices = cast.get("voices") or []
    if credit is None:
        names = ", ".join(voice.get("voice", "voice") for voice in voices) or "synthetic voices"
        engine = voices[0].get("engine", "local TTS") if voices else "local TTS"
        credit = f"Synthetic narration · {engine} voices ({names})"

    package = root / NARRATION_DIR / book_id
    package.mkdir(parents=True, exist_ok=True)
    files = []
    total = 0.0
    for number, wav in pages:
        dst = package / f"page-{number:02d}.mp3"
        encode_mp3(wav, dst, bitrate)
        seconds = duration_seconds(dst)
        total += seconds
        files.append({"page": number, "path": dst.name, "bytes": dst.stat().st_size,
                      "sha256": sha256_file(dst), "seconds": seconds})
    total = round(total, 1)

    reader = {"schema": 1, "book": book_id, "pages": len(files), "seconds": total,
              "credit": credit,
              "files": [{"page": item["page"], "src": item["path"],
                         "seconds": item["seconds"]} for item in files]}
    (package / "narration.json").write_text(
        json.dumps(reader, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    index_path = root / NARRATION_DIR / "manifest.json"
    index = {"schema": 1, "books": []}
    if index_path.is_file():
        index = json.loads(index_path.read_text(encoding="utf-8"))
    render_record = {}
    render_path = book_dir / "production/narration/render.json"
    if render_path.is_file():
        render_record = json.loads(render_path.read_text(encoding="utf-8"))
    engines = sorted({voice.get("engine") for voice in voices if voice.get("engine")})
    licence_notes = sorted({voice.get("licence_note") for voice in voices
                            if voice.get("licence_note")})
    entry = {
        "id": book_id,
        "directory": book_id,
        "pages": len(files),
        "seconds": total,
        "credit": credit,
        "engine": (f"{render_record['engine']['name']} {render_record['engine']['commit'][:7]}"
                   f" ({render_record['engine']['backend']}), {render_record['engine']['model']}"
                   if render_record.get("engine") else "unspecified"),
        "reference_engine": ", ".join(engines) or "unspecified",
        "script_sha256": sha256_file(book_dir / "production/narration/script.md"),
        "cast_sha256": sha256_file(book_dir / "production/narration/cast.json"),
        "license_note": " | ".join(licence_notes) or "unspecified; record voice rights in cast.json",
        "files": files,
    }
    index["books"] = [item for item in index["books"] if item.get("id") != book_id]
    index["books"].append(entry)
    index["books"].sort(key=lambda item: item["id"])
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")
    return {"book": book_id, "pages": len(files), "seconds": total,
            "bytes": sum(item["bytes"] for item in files),
            "package": str(package)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=str(ROOT), help="repository root")
    sub = parser.add_subparsers(dest="command", required=True)

    pack_cmd = sub.add_parser("pack", help="encode and index page audio")
    pack_cmd.add_argument("--book-dir", required=True)
    pack_cmd.add_argument("--audio", required=True)
    pack_cmd.add_argument("--book-id", required=True)
    pack_cmd.add_argument("--bitrate", default="96k")
    pack_cmd.add_argument("--credit", default=None)

    sub.add_parser("validate", help="validate packages, scripts and tag exclusion")

    sub.add_parser("hash", help="print sha256 and size").add_argument("path")

    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    try:
        if args.command == "pack":
            summary = pack(root, Path(args.book_dir).resolve(), Path(args.audio).resolve(),
                           args.book_id, args.bitrate, args.credit)
            print(f"Packed {summary['pages']} pages, {summary['seconds']}s, "
                  f"{summary['bytes']} bytes -> {summary['package']}")
        elif args.command == "validate":
            summary = validate(root)
            print(f"Narration valid: {summary['narration_books']} book(s), "
                  f"{summary['narration_files']} page files; "
                  f"scanned {summary['scanned']['epub']} EPUB(s) and "
                  f"{summary['scanned']['pdf']} PDF(s) for tags; "
                  f"declared: {', '.join(summary['declared_books']) or 'none'}")
        else:
            path = Path(args.path)
            print(f"{sha256_file(path)}  {path.stat().st_size}  {path}")
        return 0
    except NarrationError as err:
        print(f"narration: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
